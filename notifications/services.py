"""
Create notifications, respect user preferences, and push over Channels.

Services:
  - create_notification: core creation with deduplication, preferences, WebSocket push
  - push_unread_count: send updated unread counter to a user's WebSocket group
  - detect_at_risk_students: find students meeting at-risk criteria and notify
  - notify_at_risk: send at-risk notifications to parent, teacher, admin
"""
from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from typing import Any

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, Q
from django.utils import timezone

from .models import Notification, NotificationPreference

User = get_user_model()

# ─────────────────────────────────────────────────────────────────────────────
# Thresholds (configurable via settings)
# ─────────────────────────────────────────────────────────────────────────────

LOW_GRADE_PCT: float = getattr(settings, "NOTIFICATION_LOW_GRADE_PERCENT", 50.0)
AT_RISK_ABSENCE_THRESHOLD: int = getattr(settings, "NOTIFICATION_AT_RISK_ABSENCE_THRESHOLD", 3)
AT_RISK_ABSENCE_WINDOW_DAYS: int = getattr(settings, "NOTIFICATION_AT_RISK_ABSENCE_WINDOW_DAYS", 30)
AT_RISK_GRADE_PCT: float = getattr(settings, "NOTIFICATION_AT_RISK_GRADE_PERCENT", 50.0)


# ─────────────────────────────────────────────────────────────────────────────
# Preference helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_or_create_preferences(user) -> NotificationPreference:
    prefs, _ = NotificationPreference.objects.get_or_create(user=user)
    return prefs


def is_allowed(user, notification_type: str) -> bool:
    prefs = get_or_create_preferences(user)
    mapping = {
        Notification.Type.ATTENDANCE: prefs.allow_attendance,
        Notification.Type.LOW_GRADE: prefs.allow_low_grade,
        Notification.Type.AT_RISK: prefs.allow_at_risk,
        Notification.Type.EXAM_REMINDER: prefs.allow_exam_reminder,
        Notification.Type.NEW_STUDENT_REPORT: prefs.allow_student_report,
        Notification.Type.NEW_WEEKLY_REPORT: prefs.allow_weekly_report,
        Notification.Type.SYSTEM: prefs.allow_system,
    }
    return mapping.get(notification_type, True)


# ─────────────────────────────────────────────────────────────────────────────
# Core notification creation
# ─────────────────────────────────────────────────────────────────────────────

def create_notification(
    *,
    recipient,
    notification_type: str,
    title: str = "",
    body: str = "",
    title_en: str = "",
    title_ar: str = "",
    body_en: str = "",
    body_ar: str = "",
    metadata: dict[str, Any] | None = None,
    dedupe_key: str = "",
    student=None,
    broadcast: bool = True,
) -> Notification | None:
    """Create a notification, respecting preferences and deduplication.

    If a dedupe_key is supplied and a notification with that key already exists
    for the same recipient, the existing record is returned unchanged.

    After creation, the unread counter is pushed to the recipient's WebSocket
    group so the frontend can update badges instantly.
    """
    if not recipient or not recipient.is_authenticated:
        return None
    if not is_allowed(recipient, notification_type):
        return None

    meta = metadata or {}
    # Use explicit localized fields; fall back to title/body for both languages
    t_en = title_en or title
    t_ar = title_ar or title
    b_en = body_en or body
    b_ar = body_ar or body

    kwargs = {
        "recipient": recipient,
        "notification_type": notification_type,
        "title": t_en[:200],          # base field (required by DB); use English as default
        "title_en": t_en[:200],
        "title_ar": t_ar[:200],
        "body": b_en,                 # base field (required by DB); use English as default
        "body_en": b_en,
        "body_ar": b_ar,
        "metadata": meta,
        "student": student,
    }
    if dedupe_key:
        existing = Notification.objects.filter(
            recipient=recipient,
            dedupe_key=dedupe_key,
        ).first()
        if existing:
            return existing
        kwargs["dedupe_key"] = dedupe_key

    n = Notification.objects.create(**kwargs)
    if broadcast:
        push_to_websocket(n)
        push_unread_count(recipient)
    return n


# ─────────────────────────────────────────────────────────────────────────────
# Mark read / unread helpers
# ─────────────────────────────────────────────────────────────────────────────

def mark_read(notification: Notification) -> None:
    if notification.read_at is None:
        notification.read_at = timezone.now()
        notification.save(update_fields=["read_at"])
        push_unread_count(notification.recipient)


def mark_all_read(user) -> int:
    count = Notification.objects.filter(recipient=user, read_at__isnull=True).update(
        read_at=timezone.now()
    )
    if count:
        push_unread_count(user)
    return count


def get_unread_count(user) -> int:
    return Notification.objects.filter(recipient=user, read_at__isnull=True).count()


# ─────────────────────────────────────────────────────────────────────────────
# WebSocket push helpers
# ─────────────────────────────────────────────────────────────────────────────

def push_to_websocket(notification: Notification) -> None:
    layer = get_channel_layer()
    if layer is None:
        return
    from .serializers import NotificationPushSerializer

    payload = NotificationPushSerializer(notification).data
    async_to_sync(layer.group_send)(
        f"notifications_user_{notification.recipient_id}",
        {"type": "push_notification", "payload": payload},
    )


def push_unread_count(user) -> None:
    """Push the current unread notification count to the user's WS group."""
    layer = get_channel_layer()
    if layer is None:
        return
    count = get_unread_count(user)
    async_to_sync(layer.group_send)(
        f"notifications_user_{user.id}",
        {
            "type": "push_unread_count",
            "unread_count": count,
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
# At-Risk Student Detection
# ─────────────────────────────────────────────────────────────────────────────

def detect_at_risk_students():
    """
    Scan all students and return those meeting at-risk criteria:
      - Absences >= AT_RISK_ABSENCE_THRESHOLD within AT_RISK_ABSENCE_WINDOW_DAYS
      OR
      - Average grade percentage < AT_RISK_GRADE_PCT

    Returns a list of dicts: {student, reason, absences, avg_pct}
    """
    from students.models import Student
    from attendance.models import Attendance
    from exams.models import Grade

    window_start = timezone.now().date() - timedelta(days=AT_RISK_ABSENCE_WINDOW_DAYS)
    at_risk_list = []

    for student in Student.objects.select_related("user", "school_class", "parent__user").iterator():
        # Count absences in the recent window
        absence_count = Attendance.objects.filter(
            student=student,
            status=Attendance.ABSENT,
            date__gte=window_start,
        ).count()

        # Calculate average grade percentage
        grades = Grade.objects.filter(student=student).select_related("exam")
        if grades.exists():
            avg_pct = 0.0
            total_weight = 0.0
            for g in grades:
                total_grade = float(g.exam.total_grade)
                if total_grade > 0:
                    pct = float(g.score) / total_grade * 100
                    avg_pct += pct
                    total_weight += 1
            avg_pct = avg_pct / total_weight if total_weight > 0 else 0.0
        else:
            avg_pct = None  # No grades yet — can't determine low performance

        # Determine at-risk status
        is_absent_at_risk = absence_count >= AT_RISK_ABSENCE_THRESHOLD
        is_grade_at_risk = avg_pct is not None and avg_pct < AT_RISK_GRADE_PCT

        if is_absent_at_risk or is_grade_at_risk:
            reason_parts = []
            if is_absent_at_risk:
                reason_parts.append("repeated absences")
            if is_grade_at_risk:
                reason_parts.append("low academic performance")

            at_risk_list.append({
                "student": student,
                "reason": " and ".join(reason_parts),
                "absences": absence_count,
                "avg_pct": round(avg_pct, 1) if avg_pct is not None else None,
            })

    return at_risk_list


def notify_at_risk(student, reason: str, absences: int, avg_pct: float | None):
    """
    Send at-risk notifications to Parent, Teacher(s), and Admin.
    NOT to the student themselves (per requirements).

    Dedupe keys include today's date so that daily scans can re-flag
    a student whose situation has worsened, while still preventing
    duplicate notifications within the same day.
    """
    today_str = timezone.now().date().isoformat()
    student_name = student.user.get_full_name() or student.student_id or str(student.pk)
    class_name = student.school_class.display_name if student.school_class else "—"

    # Build reason text
    reason_en = f"due to {reason}"
    reason_ar_parts = []
    if "absences" in reason:
        reason_ar_parts.append("الغياب المتكرر")
    if "academic" in reason or "performance" in reason:
        reason_ar_parts.append("ضعف الأداء الدراسي")
    reason_ar = f"بسبب {' و '.join(reason_ar_parts)}" if reason_ar_parts else reason_en

    common_meta = {
        "student_id": student.student_id,
        "class": class_name,
        "absences": absences,
        "avg_pct": avg_pct,
        "reason": reason,
    }

    # ── PARENT ───────────────────────────────────────────────────────────────
    parent = getattr(student, "parent", None)
    if parent and getattr(parent, "user_id", None):
        create_notification(
            recipient=parent.user,
            notification_type=Notification.Type.AT_RISK,
            title_en="At-Risk Student Alert",
            title_ar="تنبيه طالب في خطر",
            body_en=f"{student_name} has been flagged as an At-Risk Student {reason_en}.",
            body_ar=f"تم تصنيف {student_name} كطالب في خطر {reason_ar}.",
            metadata=common_meta,
            dedupe_key=f"atrisk_{student.id}_{today_str}_parent_{parent.id}",
            student=student,
        )

    # ── TEACHERS assigned to the student's class ─────────────────────────────
    school_class = getattr(student, "school_class", None)
    if school_class:
        for teacher in school_class.teachers.select_related("user").all():
            if teacher.user_id:
                create_notification(
                    recipient=teacher.user,
                    notification_type=Notification.Type.AT_RISK,
                    title_en="At-Risk Student Alert",
                    title_ar="تنبيه طالب في خطر",
                    body_en=f"{student_name} has been flagged as an At-Risk Student {reason_en}.",
                    body_ar=f"تم تصنيف {student_name} كطالب في خطر {reason_ar}.",
                    metadata=common_meta,
                    dedupe_key=f"atrisk_{student.id}_{today_str}_teacher_{teacher.id}",
                    student=student,
                )

    # ── ADMINS ───────────────────────────────────────────────────────────────
    for admin_user in User.objects.filter(role=User.Role.ADMIN):
        create_notification(
            recipient=admin_user,
            notification_type=Notification.Type.AT_RISK,
            title_en="At-Risk Student Alert",
            title_ar="تنبيه طالب في خطر",
            body_en=f"{student_name} has been flagged as an At-Risk Student {reason_en}.",
            body_ar=f"تم تصنيف {student_name} كطالب في خطر {reason_ar}.",
            metadata=common_meta,
            dedupe_key=f"atrisk_{student.id}_{today_str}_admin_{admin_user.id}",
            student=student,
        )


def run_at_risk_detection():
    """Full at-risk scan: detect and notify all at-risk students."""
    at_risk_list = detect_at_risk_students()
    for entry in at_risk_list:
        notify_at_risk(
            student=entry["student"],
            reason=entry["reason"],
            absences=entry["absences"],
            avg_pct=entry["avg_pct"],
        )
    return len(at_risk_list)
