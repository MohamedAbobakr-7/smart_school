from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from attendance.models import Attendance
from exams.models import Grade
from reports.models import Report, WeeklyReport
from users.models import User

from .models import Notification
from . import services

LOW_GRADE_PCT = getattr(settings, "NOTIFICATION_LOW_GRADE_PERCENT", 60.0)


def _notify_users_for_student(student, include_teachers=True, subject=None, **kwargs):
    users = {student.user}
    if getattr(student, "parent_id", None) and student.parent and student.parent.user_id:
        users.add(student.parent.user)
        
    if include_teachers and getattr(student, "school_class", None):
        # Notify teachers assigned to this student's class
        teachers = student.school_class.teachers.all()
        if subject:
            # If subject is provided, filter teachers who teach this subject
            teachers = teachers.filter(assigned_subjects=subject)
            
        for t in teachers:
            if t.user_id:
                users.add(t.user)
                
    return list(users)


@receiver(post_save, sender=Grade)
def notify_low_grade(sender, instance: Grade, **kwargs):
    try:
        pct = float(instance.get_percentage())
    except Exception:
        return
    if pct >= LOW_GRADE_PCT:
        return
    student = instance.student
    exam = instance.exam
    subj = exam.subject
    for u in _notify_users_for_student(student, include_teachers=True, subject=subj):
        services.create_notification(
            recipient=u,
            notification_type=Notification.Type.LOW_GRADE,
            title_en="Low grade alert",
            title_ar="تنبيه درجة متدنية",
            body_en=f"{exam.name} ({subj}): {pct:.1f}% — consider review or extra practice.",
            body_ar=f"{exam.name} ({subj}): {pct:.1f}% — يُنصح بالمراجعة أو المزيد من التمارين.",
            metadata={
                "grade_id": instance.id,
                "exam_id": exam.id,
                "subject": subj.name,
                "percentage": pct,
            },
            dedupe_key=f"lowgrade_grade_{instance.id}",
        )


@receiver(post_save, sender=Attendance)
def notify_attendance_absence(sender, instance: Attendance, **kwargs):
    if instance.status != Attendance.ABSENT:
        return
    student = instance.student
    d = instance.date.isoformat()
    for u in _notify_users_for_student(student, include_teachers=True):
        services.create_notification(
            recipient=u,
            notification_type=Notification.Type.ATTENDANCE,
            title_en="Attendance: marked absent",
            title_ar="الحضور: تم تسجيل الغياب",
            body_en=f"{student.student_id} was marked absent on {d}.",
            body_ar=f"تم تسجيل غياب {student.student_id} في {d}.",
            metadata={
                "attendance_id": instance.id,
                "student_id": student.student_id,
                "date": d,
            },
            dedupe_key=f"absent_{student.id}_{d}_u{u.id}",
        )


@receiver(post_save, sender=Report)
def notify_new_student_report(sender, instance: Report, created, **kwargs):
    if not created:
        return
    student = instance.student
    content_preview = (instance.content[:500] + "…") if len(instance.content) > 500 else instance.content
    for u in _notify_users_for_student(student, include_teachers=True):
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
        )


@receiver(post_save, sender=WeeklyReport)
def notify_weekly_report_ready(sender, instance: WeeklyReport, **kwargs):
    if instance.status != WeeklyReport.Status.READY:
        return
    rate = (instance.attendance_stats or {}).get('attendance_rate_percent', '—')
    title_en = (
        "School weekly report"
        if instance.scope == WeeklyReport.Scope.SCHOOL
        else "Your weekly teaching report"
    )
    title_ar = (
        "التقرير الأسبوعي للمدرسة"
        if instance.scope == WeeklyReport.Scope.SCHOOL
        else "تقريرك الأسبوعي للتدريس"
    )
    body_en = f"Week {instance.week_start} – {instance.week_end}: attendance rate {rate}%."
    body_ar = f"الأسبوع {instance.week_start} – {instance.week_end}: معدل الحضور {rate}%."
    meta = {
        "weekly_report_id": instance.id,
        "scope": instance.scope,
        "week_start": str(instance.week_start),
    }
    if instance.scope == WeeklyReport.Scope.SCHOOL:
        for u in User.objects.filter(role=User.Role.ADMIN):
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
