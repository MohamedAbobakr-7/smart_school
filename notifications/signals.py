"""
Automatic role-based notification signals for the Smart School platform.

Signals fire on:
  - Attendance creation/update  →  absence alerts (STUDENT, PARENT, TEACHER, ADMIN)
  - Grade creation/update       →  low-grade alerts (STUDENT, PARENT, TEACHER, ADMIN)
  - Report creation             →  new-report alert
  - WeeklyReport status→READY   →  weekly-report alert

After attendance/grade events, at-risk detection is also triggered for the
affected student.

Deduplication is always enforced per-recipient via a unique dedupe_key so the
same event never produces two notifications for the same user, even if the
signal fires multiple times (e.g. update_fields triggers).
"""
from __future__ import annotations

from django.conf import settings
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from attendance.models import Attendance
from exams.models import Grade
from reports.models import Report, WeeklyReport
from users.models import User

from .models import Notification
from . import services

# Threshold: percentage at or below which a grade is considered "low".
LOW_GRADE_PCT: float = getattr(settings, "NOTIFICATION_LOW_GRADE_PERCENT", 50.0)


# ─────────────────────────────────────────────────────────────────────────────
# Helper: collect admin users (cached per call — admins are few)
# ─────────────────────────────────────────────────────────────────────────────

def _admin_users():
    return list(User.objects.filter(role=User.Role.ADMIN).select_related())


# ─────────────────────────────────────────────────────────────────────────────
# Helper: teachers assigned to a student's class
# ─────────────────────────────────────────────────────────────────────────────

def _class_teachers(student, subject=None):
    school_class = getattr(student, "school_class", None)
    if not school_class:
        return []
    qs = school_class.teachers.select_related("user").all()
    if subject:
        qs = qs.filter(assigned_subjects=subject)
    return [t for t in qs if t.user_id]


# ─────────────────────────────────────────────────────────────────────────────
# Track previous Attendance.status so we only react to genuine ABSENT events
# ─────────────────────────────────────────────────────────────────────────────

@receiver(pre_save, sender=Attendance)
def _cache_attendance_previous_status(sender, instance, **kwargs):
    """Store the previous status on the instance for post_save comparison."""
    if instance.pk:
        try:
            instance._prev_status = Attendance.objects.filter(pk=instance.pk).values_list("status", flat=True).get()
        except Attendance.DoesNotExist:
            instance._prev_status = None
    else:
        instance._prev_status = None


# ─────────────────────────────────────────────────────────────────────────────
# Attendance → absence notifications
# ─────────────────────────────────────────────────────────────────────────────

@receiver(post_save, sender=Attendance)
def notify_attendance_absence(sender, instance: Attendance, created, **kwargs):
    """
    Fire notifications when a student is recorded as ABSENT.

    Message examples (per role):
      Student: "You were marked absent today."
      Parent:  "Ahmed Hassan was absent today from Grade 3-A."
      Teacher: "Ahmed Hassan was absent today from your class."
      Admin:   "Attendance alert: Ahmed Hassan was absent from Grade 3-A."

    Guards:
    - Only fires if the final status is ABSENT.
    - For updates: only fires if status changed *to* ABSENT (not re-saving the
      same absent record unchanged).
    """
    if instance.status != Attendance.ABSENT:
        return

    # For updates, only proceed if status changed to ABSENT
    prev = getattr(instance, "_prev_status", None)
    if not created and prev == Attendance.ABSENT:
        # Re-saving an already-absent record — skip to avoid duplicates
        return

    student = instance.student
    date_str = instance.date.isoformat()
    student_name = student.user.get_full_name() or student.student_id or str(student.pk)
    class_name = student.school_class.display_name if student.school_class else "—"

    common_meta = {
        "attendance_id": instance.id,
        "student_id": student.student_id,
        "date": date_str,
        "class": class_name,
    }

    # ── STUDENT ──────────────────────────────────────────────────────────────
    services.create_notification(
        recipient=student.user,
        notification_type=Notification.Type.ATTENDANCE,
        title_en="You were marked absent",
        title_ar="تم تسجيل غيابك",
        body_en="You were marked absent today.",
        body_ar="تم تسجيل غيابك اليوم.",
        metadata=common_meta,
        dedupe_key=f"absent_{student.id}_{date_str}_student",
        student=student,
    )

    # ── PARENT ───────────────────────────────────────────────────────────────
    parent = getattr(student, "parent", None)
    if parent and getattr(parent, "user_id", None):
        services.create_notification(
            recipient=parent.user,
            notification_type=Notification.Type.ATTENDANCE,
            title_en="Absence Alert",
            title_ar="تنبيه غياب",
            body_en=f"{student_name} was absent today from {class_name}.",
            body_ar=f"تغيّب {student_name} اليوم من {class_name}.",
            metadata=common_meta,
            dedupe_key=f"absent_{student.id}_{date_str}_parent_{parent.id}",
            student=student,
        )

    # ── TEACHERS in the student's class ──────────────────────────────────────
    for teacher in _class_teachers(student):
        services.create_notification(
            recipient=teacher.user,
            notification_type=Notification.Type.ATTENDANCE,
            title_en="Student Absent",
            title_ar="غياب طالب",
            body_en=f"{student_name} was absent today from your class.",
            body_ar=f"تغيّب {student_name} اليوم من حصتك.",
            metadata=common_meta,
            dedupe_key=f"absent_{student.id}_{date_str}_teacher_{teacher.id}",
            student=student,
        )

    # ── ADMINS ───────────────────────────────────────────────────────────────
    for admin_user in _admin_users():
        services.create_notification(
            recipient=admin_user,
            notification_type=Notification.Type.ATTENDANCE,
            title_en="Attendance Alert",
            title_ar="تنبيه حضور",
            body_en=f"Attendance alert: {student_name} was absent from {class_name}.",
            body_ar=f"تنبيه حضور: تغيّب {student_name} من {class_name}.",
            metadata=common_meta,
            dedupe_key=f"absent_{student.id}_{date_str}_admin_{admin_user.id}",
            student=student,
        )

    # ── Trigger at-risk detection for this student ───────────────────────────
    _check_at_risk_after_absence(student)


# ─────────────────────────────────────────────────────────────────────────────
# Grade → low-grade notifications
# ─────────────────────────────────────────────────────────────────────────────

@receiver(post_save, sender=Grade)
def notify_low_grade(sender, instance: Grade, **kwargs):
    """
    Fire notifications when a student's grade percentage is at or below LOW_GRADE_PCT.

    Uses percentage-based logic: grade_percentage = (score / exam.total_grade) * 100

    Validation:
      - A score of 45/50 (90%) must NOT trigger a low-grade notification.
      - A score of 40/100 (40%) must trigger a low-grade notification.

    Message example:
      "Ahmed Hassan scored 42% in Mathematics and requires attention."

    Recipients: STUDENT, PARENT, TEACHER (who created the exam), ADMIN.
    Deduplication: per grade record per user — so updating a grade only sends
    one notification total per recipient.
    """
    try:
        pct = float(instance.get_percentage())
    except Exception:
        return

    if pct > LOW_GRADE_PCT:
        return

    student = instance.student
    exam = instance.exam
    subject = exam.subject
    total = float(exam.total_grade)
    score = float(instance.score)
    student_name = student.user.get_full_name() or student.student_id or str(student.pk)
    pct_int = int(round(pct))

    common_meta = {
        "grade_id": instance.id,
        "exam_id": exam.id,
        "subject": subject.name,
        "percentage": round(pct, 1),
        "score": score,
        "total": total,
        "student_id": student.student_id,
    }

    # ── STUDENT ──────────────────────────────────────────────────────────────
    services.create_notification(
        recipient=student.user,
        notification_type=Notification.Type.LOW_GRADE,
        title_en="Low Grade Alert",
        title_ar="تنبيه درجة منخفضة",
        body_en=f"You scored {pct_int}% in {subject.name} and requires attention.",
        body_ar=f"حصلت على {pct_int}% في {subject.name} ويحتاج إلى اهتمام.",
        metadata=common_meta,
        dedupe_key=f"lowgrade_{instance.id}_student_{student.id}",
        student=student,
    )

    # ── PARENT ───────────────────────────────────────────────────────────────
    parent = getattr(student, "parent", None)
    if parent and getattr(parent, "user_id", None):
        services.create_notification(
            recipient=parent.user,
            notification_type=Notification.Type.LOW_GRADE,
            title_en="Low Grade Alert",
            title_ar="تنبيه درجة منخفضة",
            body_en=f"{student_name} scored {pct_int}% in {subject.name} and requires attention.",
            body_ar=f"حصل {student_name} على {pct_int}% في {subject.name} ويحتاج إلى اهتمام.",
            metadata=common_meta,
            dedupe_key=f"lowgrade_{instance.id}_parent_{parent.id}",
            student=student,
        )

    # ── TEACHER who owns the exam ─────────────────────────────────────────────
    if exam.teacher_id and exam.teacher.user_id:
        services.create_notification(
            recipient=exam.teacher.user,
            notification_type=Notification.Type.LOW_GRADE,
            title_en="Low Grade Alert",
            title_ar="تنبيه درجة منخفضة",
            body_en=f"{student_name} scored {pct_int}% in {subject.name} and requires attention.",
            body_ar=f"حصل {student_name} على {pct_int}% في {subject.name} ويحتاج إلى اهتمام.",
            metadata=common_meta,
            dedupe_key=f"lowgrade_{instance.id}_teacher_{exam.teacher_id}",
            student=student,
        )

    # ── ADMINS ───────────────────────────────────────────────────────────────
    for admin_user in _admin_users():
        services.create_notification(
            recipient=admin_user,
            notification_type=Notification.Type.LOW_GRADE,
            title_en="Low Grade Alert",
            title_ar="تنبيه درجة منخفضة",
            body_en=f"{student_name} scored {pct_int}% in {subject.name} and requires attention.",
            body_ar=f"حصل {student_name} على {pct_int}% في {subject.name} ويحتاج إلى اهتمام.",
            metadata=common_meta,
            dedupe_key=f"lowgrade_{instance.id}_admin_{admin_user.id}",
            student=student,
        )

    # ── Trigger at-risk detection for this student ───────────────────────────
    _check_at_risk_after_grade(student)


# ─────────────────────────────────────────────────────────────────────────────
# At-Risk triggers after attendance/grade events
# ─────────────────────────────────────────────────────────────────────────────

def _check_at_risk_after_absence(student):
    """After an absence event, check if the student now meets at-risk criteria."""
    from attendance.models import Attendance as Att
    from datetime import timedelta
    from django.utils import timezone

    window_days = getattr(settings, "NOTIFICATION_AT_RISK_ABSENCE_WINDOW_DAYS", 30)
    threshold = getattr(settings, "NOTIFICATION_AT_RISK_ABSENCE_THRESHOLD", 3)

    window_start = timezone.now().date() - timedelta(days=window_days)
    absence_count = Att.objects.filter(
        student=student,
        status=Att.ABSENT,
        date__gte=window_start,
    ).count()

    if absence_count >= threshold:
        # Check if we already have an at-risk notification for this student recently
        # (dedupe_key pattern prevents duplicates within the same window)
        services.notify_at_risk(
            student=student,
            reason="repeated absences",
            absences=absence_count,
            avg_pct=None,
        )


def _check_at_risk_after_grade(student):
    """After a low-grade event, check if the student now meets at-risk criteria."""
    from exams.models import Grade

    grade_pct_threshold = getattr(settings, "NOTIFICATION_AT_RISK_GRADE_PERCENT", 50.0)

    grades = Grade.objects.filter(student=student).select_related("exam")
    if not grades.exists():
        return

    total_weight = 0.0
    total_pct = 0.0
    for g in grades:
        total_grade = float(g.exam.total_grade)
        if total_grade > 0:
            total_pct += float(g.score) / total_grade * 100
            total_weight += 1

    avg_pct = total_pct / total_weight if total_weight > 0 else 0.0

    if avg_pct < grade_pct_threshold:
        # Also check absences to build a combined reason
        from attendance.models import Attendance as Att
        from datetime import timedelta
        from django.utils import timezone

        window_days = getattr(settings, "NOTIFICATION_AT_RISK_ABSENCE_WINDOW_DAYS", 30)
        absence_threshold = getattr(settings, "NOTIFICATION_AT_RISK_ABSENCE_THRESHOLD", 3)
        window_start = timezone.now().date() - timedelta(days=window_days)
        absence_count = Att.objects.filter(
            student=student,
            status=Att.ABSENT,
            date__gte=window_start,
        ).count()

        reason_parts = []
        if absence_count >= absence_threshold:
            reason_parts.append("repeated absences")
        reason_parts.append("low academic performance")

        services.notify_at_risk(
            student=student,
            reason=" and ".join(reason_parts),
            absences=absence_count,
            avg_pct=round(avg_pct, 1),
        )


# ─────────────────────────────────────────────────────────────────────────────
# Report → new student report notifications
# ─────────────────────────────────────────────────────────────────────────────

@receiver(post_save, sender=Report)
def notify_new_student_report(sender, instance: Report, created, **kwargs):
    if not created:
        return
    student = instance.student
    content_preview = (instance.content[:500] + "…") if len(instance.content) > 500 else instance.content
    student_name = student.user.get_full_name() or student.student_id or str(student.pk)

    recipients = [student.user]
    parent = getattr(student, "parent", None)
    if parent and getattr(parent, "user_id", None):
        recipients.append(parent.user)
    for teacher in _class_teachers(student):
        recipients.append(teacher.user)

    for u in recipients:
        services.create_notification(
            recipient=u,
            notification_type=Notification.Type.NEW_STUDENT_REPORT,
            title_en=f"New report: {instance.title}",
            title_ar=f"تقرير جديد: {instance.title}",
            body_en=content_preview,
            body_ar=content_preview,
            metadata={
                "report_id": instance.id,
                "report_type": instance.report_type,
                "student_id": student.student_id,
            },
            dedupe_key=f"report_{instance.id}_u{u.id}",
            student=student,
        )


# ─────────────────────────────────────────────────────────────────────────────
# WeeklyReport → weekly report ready notifications
# ─────────────────────────────────────────────────────────────────────────────

@receiver(post_save, sender=WeeklyReport)
def notify_weekly_report_ready(sender, instance: WeeklyReport, **kwargs):
    if instance.status != WeeklyReport.Status.READY:
        return

    rate = (instance.attendance_stats or {}).get("attendance_rate_percent", "—")
    body_en = f"Week {instance.week_start} – {instance.week_end}: attendance rate {rate}%."
    body_ar = f"الأسبوع {instance.week_start} – {instance.week_end}: معدل الحضور {rate}%."
    meta = {
        "weekly_report_id": instance.id,
        "scope": instance.scope,
        "week_start": str(instance.week_start),
    }

    if instance.scope == WeeklyReport.Scope.SCHOOL:
        title_en = "School weekly report"
        title_ar = "التقرير الأسبوعي للمدرسة"
        for u in _admin_users():
            services.create_notification(
                recipient=u,
                notification_type=Notification.Type.NEW_WEEKLY_REPORT,
                title_en=title_en,
                title_ar=title_ar,
                body_en=body_en,
                body_ar=body_ar,
                metadata=meta,
                dedupe_key=f"weekly_{instance.dedupe_key}_admin_{u.id}",
            )
    elif instance.teacher_id:
        title_en = "Your weekly teaching report"
        title_ar = "تقريرك الأسبوعي للتدريس"
        tu = instance.teacher.user
        services.create_notification(
            recipient=tu,
            notification_type=Notification.Type.NEW_WEEKLY_REPORT,
            title_en=title_en,
            title_ar=title_ar,
            body_en=body_en,
            body_ar=body_ar,
            metadata=meta,
            dedupe_key=f"weekly_{instance.dedupe_key}_teacher",
        )
