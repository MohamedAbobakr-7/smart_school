"""
Management command: send_exam_reminders

Sends exam reminder notifications to students, teachers, and admins for upcoming exams.

Usage:
    python manage.py send_exam_reminders
    python manage.py send_exam_reminders --days 1 3 7

Schedule this command via cron or Windows Task Scheduler to run once daily:
    # Linux/Mac cron (daily at 7am)
    0 7 * * * /path/to/venv/bin/python /path/to/manage.py send_exam_reminders

    # Windows Task Scheduler: run daily, action:
    python manage.py send_exam_reminders
"""
from __future__ import annotations

from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db.models import Q

from exams.models import Exam
from notifications.models import Notification
from notifications import services
from users.models import User


class Command(BaseCommand):
    help = "Send exam reminder notifications for exams N days ahead (default: 1 and 3 days)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            nargs="+",
            type=int,
            default=[1, 3],
            help="How many days ahead to look for exams (default: 1 3).",
        )

    def handle(self, *args, **options):
        days_list: list[int] = options["days"]
        today = date.today()
        total_sent = 0

        admin_users = list(User.objects.filter(role=User.Role.ADMIN))

        for days_ahead in days_list:
            target_date = today + timedelta(days=days_ahead)
            exams = (
                Exam.objects
                .filter(exam_date=target_date)
                .select_related("subject", "teacher__user")
            )

            for exam in exams:
                exam_label = f"{exam.name} ({exam.subject.name})"
                exam_date_str = exam.exam_date.isoformat()

                # ── Students enrolled in the exam's class (via class_id string) ──
                student_qs = self._get_students_for_exam(exam)
                for student in student_qs:
                    dk = f"examreminder_{exam.id}_days{days_ahead}_student_{student.id}"
                    n = services.create_notification(
                        recipient=student.user,
                        notification_type=Notification.Type.EXAM_REMINDER,
                        title_en=f"Exam Reminder: {exam_label}",
                        title_ar=f"تذكير بالاختبار: {exam_label}",
                        body_en=(
                            f"You have an upcoming exam: {exam.name} in {exam.subject.name} "
                            f"on {exam_date_str} ({exam.get_exam_type_display()}, {exam.duration} min)."
                        ),
                        body_ar=(
                            f"لديك اختبار قادم: {exam.name} في {exam.subject.name} "
                            f"بتاريخ {exam_date_str} ({exam.get_exam_type_display()}، {exam.duration} دقيقة)."
                        ),
                        metadata={
                            "exam_id": exam.id,
                            "exam_date": exam_date_str,
                            "subject": exam.subject.name,
                            "days_ahead": days_ahead,
                        },
                        dedupe_key=dk,
                    )
                    if n and n.pk:
                        total_sent += 1

                    # Also remind the student's parent
                    parent = getattr(student, "parent", None)
                    if parent and getattr(parent, "user_id", None):
                        student_name = student.user.get_full_name() or student.student_id
                        dk_parent = f"examreminder_{exam.id}_days{days_ahead}_parent_{parent.id}_student_{student.id}"
                        np = services.create_notification(
                            recipient=parent.user,
                            notification_type=Notification.Type.EXAM_REMINDER,
                            title_en=f"Exam Reminder for {student_name}",
                            title_ar=f"تذكير باختبار {student_name}",
                            body_en=(
                                f"{student_name} has an upcoming exam: {exam.name} "
                                f"in {exam.subject.name} on {exam_date_str}."
                            ),
                            body_ar=(
                                f"لدى {student_name} اختبار قادم: {exam.name} "
                                f"في {exam.subject.name} بتاريخ {exam_date_str}."
                            ),
                            metadata={
                                "exam_id": exam.id,
                                "exam_date": exam_date_str,
                                "subject": exam.subject.name,
                                "days_ahead": days_ahead,
                                "student_id": student.student_id,
                            },
                            dedupe_key=dk_parent,
                        )
                        if np and np.pk:
                            total_sent += 1

                # ── Teacher who owns the exam ──────────────────────────────
                if exam.teacher_id and exam.teacher.user_id:
                    dk_teacher = f"examreminder_{exam.id}_days{days_ahead}_teacher_{exam.teacher_id}"
                    nt = services.create_notification(
                        recipient=exam.teacher.user,
                        notification_type=Notification.Type.EXAM_REMINDER,
                        title_en=f"Upcoming Exam: {exam_label}",
                        title_ar=f"اختبار قادم: {exam_label}",
                        body_en=(
                            f"Your exam '{exam.name}' ({exam.subject.name}) is scheduled "
                            f"for {exam_date_str} in {days_ahead} day(s)."
                        ),
                        body_ar=(
                            f"اختبارك '{exam.name}' ({exam.subject.name}) مقرر "
                            f"بتاريخ {exam_date_str} خلال {days_ahead} يوم/أيام."
                        ),
                        metadata={
                            "exam_id": exam.id,
                            "exam_date": exam_date_str,
                            "subject": exam.subject.name,
                            "days_ahead": days_ahead,
                        },
                        dedupe_key=dk_teacher,
                    )
                    if nt and nt.pk:
                        total_sent += 1

                # ── Admins ─────────────────────────────────────────────────
                for admin_user in admin_users:
                    dk_admin = f"examreminder_{exam.id}_days{days_ahead}_admin_{admin_user.id}"
                    na = services.create_notification(
                        recipient=admin_user,
                        notification_type=Notification.Type.EXAM_REMINDER,
                        title_en=f"Upcoming Exam: {exam_label}",
                        title_ar=f"اختبار قادم: {exam_label}",
                        body_en=(
                            f"Exam '{exam.name}' ({exam.subject.name}) is scheduled "
                            f"for {exam_date_str} in {days_ahead} day(s)."
                        ),
                        body_ar=(
                            f"الاختبار '{exam.name}' ({exam.subject.name}) مقرر "
                            f"بتاريخ {exam_date_str} خلال {days_ahead} يوم/أيام."
                        ),
                        metadata={
                            "exam_id": exam.id,
                            "exam_date": exam_date_str,
                            "subject": exam.subject.name,
                            "days_ahead": days_ahead,
                        },
                        dedupe_key=dk_admin,
                    )
                    if na and na.pk:
                        total_sent += 1

                self.stdout.write(
                    f"  [{days_ahead}d] {exam_label} on {exam_date_str} — "
                    f"processed {student_qs.count()} students."
                )

        self.stdout.write(
            self.style.SUCCESS(f"Done. {total_sent} new notification(s) created.")
        )

    def _get_students_for_exam(self, exam: Exam):
        """
        Return students relevant to this exam.
        Uses class_id string on Exam to find students with matching class_id,
        or falls back to all students enrolled in the exam's subject.
        """
        from students.models import Student

        if exam.class_id:
            # Match students by the string class_id on their profile
            qs = Student.objects.filter(
                class_id=exam.class_id
            ).select_related("user", "parent__user")
        else:
            # Fallback: all students enrolled in the subject
            qs = Student.objects.filter(
                subjects=exam.subject
            ).select_related("user", "parent__user")

        return qs
