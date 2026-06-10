"""
Management command: test_notifications

Diagnostic script that creates test data and verifies the notification system:
  - Marking a student absent → ATTENDANCE notifications for all 4 roles
  - Creating a grade below 50% → LOW_GRADE notifications for all 4 roles
  - Creating a grade above 50% (45/50 = 90%) → NO low-grade notification
  - At-risk detection → AT_RISK notifications for parent, teacher, admin (NOT student)

Usage:
    python manage.py test_notifications
"""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from students.models import Student
from teachers.models import Teacher
from parents.models import Parent
from classes.models import SchoolClass
from subjects.models import Subject
from attendance.models import Attendance
from exams.models import Exam, Grade
from notifications.models import Notification, NotificationPreference
from notifications.services import run_at_risk_detection

User = get_user_model()


class Command(BaseCommand):
    help = "Diagnostic test: create test data and verify the notification system works."

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("NOTIFICATION SYSTEM DIAGNOSTIC TEST")
        self.stdout.write("=" * 60)

        self._cleanup_test_data()
        data = self._create_test_data()

        att_count = self._test_attendance_notification(data)
        grade_count = self._test_low_grade_notification(data)
        atrisk_count = self._test_at_risk_notification(data)

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("SUMMARY")
        self.stdout.write("=" * 60)
        total_new = att_count + grade_count + atrisk_count
        self.stdout.write(f"  Attendance notifications: {att_count}")
        self.stdout.write(f"  Low-grade notifications:  {grade_count}")
        self.stdout.write(f"  At-risk notifications:    {atrisk_count}")
        self.stdout.write(f"  Total new notifications:  {total_new}")

        if total_new > 0:
            self.stdout.write(self.style.SUCCESS("\nNOTIFICATION SYSTEM IS WORKING"))
        else:
            self.stdout.write(self.style.ERROR("\nNOTIFICATION SYSTEM IS NOT WORKING - 0 notifications created!"))

        self.stdout.write("\nCleaning up test data...")
        self._cleanup_test_data()
        self.stdout.write(self.style.SUCCESS("Done."))

    # ─────────────────────────────────────────────────────────────────────────
    # Cleanup
    # ─────────────────────────────────────────────────────────────────────────

    def _cleanup_test_data(self):
        """Remove any test data from previous runs."""
        # Delete in order to respect FK constraints
        Notification.objects.filter(metadata__test_run=True).delete()
        Grade.objects.filter(student__student_id__startswith="TESTNOTIF").delete()
        Exam.objects.filter(name__startswith="TESTNOTIF").delete()
        Attendance.objects.filter(student__student_id__startswith="TESTNOTIF").delete()
        Student.objects.filter(student_id__startswith="TESTNOTIF").delete()
        Teacher.objects.filter(teacher_id__startswith="TESTNOTIF").delete()
        Parent.objects.filter(parent_id__startswith="TESTNOTIF").delete()
        SchoolClass.objects.filter(name__startswith="Test Grade").delete()
        Subject.objects.filter(code__startswith="TESTNOTIF").delete()
        User.objects.filter(username__startswith="testnotif_").delete()

    # ─────────────────────────────────────────────────────────────────────────
    # Create test data
    # ─────────────────────────────────────────────────────────────────────────

    @transaction.atomic
    def _create_test_data(self):
        """Create minimal test data to exercise the notification system."""
        self.stdout.write("\n=== Creating test data ===")

        # ── Admin user ──────────────────────────────────────────────────────
        admin_user, _ = User.objects.get_or_create(
            username="testnotif_admin",
            defaults={
                "first_name": "Admin",
                "last_name": "User",
                "role": User.Role.ADMIN,
                "email": "testnotif_admin@school.com",
            },
        )
        admin_user.set_password("testpass123")
        admin_user.save()
        self.stdout.write(f"  Admin: {admin_user} (id={admin_user.id})")

        # ── SchoolClass ─────────────────────────────────────────────────────
        school_class, _ = SchoolClass.objects.get_or_create(
            name="Test Grade 3",
            section="A",
            defaults={"description": "Test class for notification testing"},
        )
        self.stdout.write(f"  Class: {school_class} (id={school_class.id})")

        # ── Subject ─────────────────────────────────────────────────────────
        subject, _ = Subject.objects.get_or_create(
            code="TESTNOTIF_MATH",
            defaults={"name": "Test Mathematics", "description": "Test subject"},
        )
        self.stdout.write(f"  Subject: {subject} (id={subject.id})")

        # ── Parent ──────────────────────────────────────────────────────────
        parent_user, _ = User.objects.get_or_create(
            username="testnotif_parent",
            defaults={
                "first_name": "Parent",
                "last_name": "Hassan",
                "role": User.Role.PARENT,
                "email": "testnotif_parent@school.com",
            },
        )
        parent_user.set_password("testpass123")
        parent_user.save()
        parent, _ = Parent.objects.get_or_create(
            parent_id="TESTNOTIF_P001",
            defaults={"user": parent_user, "occupation": "Engineer", "relationship": "Father"},
        )
        self.stdout.write(f"  Parent: {parent} (id={parent.id})")

        # ── Teacher ─────────────────────────────────────────────────────────
        teacher_user, _ = User.objects.get_or_create(
            username="testnotif_teacher",
            defaults={
                "first_name": "Teacher",
                "last_name": "Ali",
                "role": User.Role.TEACHER,
                "email": "testnotif_teacher@school.com",
            },
        )
        teacher_user.set_password("testpass123")
        teacher_user.save()
        teacher, _ = Teacher.objects.get_or_create(
            teacher_id="TESTNOTIF_T001",
            defaults={"user": teacher_user},
        )
        teacher.assigned_classes.add(school_class)
        teacher.assigned_subjects.add(subject)
        self.stdout.write(f"  Teacher: {teacher} (id={teacher.id})")

        # ── Student ─────────────────────────────────────────────────────────
        student_user, _ = User.objects.get_or_create(
            username="testnotif_student",
            defaults={
                "first_name": "Ahmed",
                "last_name": "Hassan",
                "role": User.Role.STUDENT,
                "email": "testnotif_student@school.com",
            },
        )
        student_user.set_password("testpass123")
        student_user.save()
        student, _ = Student.objects.get_or_create(
            student_id="TESTNOTIF_S001",
            defaults={
                "user": student_user,
                "parent": parent,
                "school_class": school_class,
                "class_level": "Grade 3",
            },
        )
        student.subjects.add(subject)
        self.stdout.write(f"  Student: {student} (id={student.id}), class={student.school_class}")

        # ── Ensure notification preferences are enabled ─────────────────────
        for u in [admin_user, parent_user, teacher_user, student_user]:
            prefs, _ = NotificationPreference.objects.get_or_create(user=u)
            prefs.allow_attendance = True
            prefs.allow_low_grade = True
            prefs.allow_at_risk = True
            prefs.allow_exam_reminder = True
            prefs.save()
            self.stdout.write(f"  Preferences for {u.username}: all enabled")

        return {
            "admin": admin_user,
            "parent": parent,
            "parent_user": parent_user,
            "teacher": teacher,
            "teacher_user": teacher_user,
            "student": student,
            "student_user": student_user,
            "school_class": school_class,
            "subject": subject,
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Test 1: Attendance Notification
    # ─────────────────────────────────────────────────────────────────────────

    @transaction.atomic
    def _test_attendance_notification(self, data):
        """Test: marking a student absent should create notifications for all 4 roles."""
        self.stdout.write("\n=== Test 1: Attendance Notification ===")
        student = data["student"]
        today = date.today()

        # Clear any existing attendance for today to avoid unique constraint
        Attendance.objects.filter(student=student, date=today).delete()

        before_count = Notification.objects.count()
        self.stdout.write(f"  Notifications before: {before_count}")

        # Create an ABSENT attendance record — this should trigger the signal
        att = Attendance.objects.create(student=student, date=today, status=Attendance.ABSENT)
        self.stdout.write(f"  Created attendance: id={att.id}, status={att.status}")

        after_count = Notification.objects.count()
        new_count = after_count - before_count
        self.stdout.write(f"  Notifications after: {after_count}")
        self.stdout.write(f"  New notifications created: {new_count}")

        # Check each role
        for role_name, user in [
            ("Student", data["student_user"]),
            ("Parent", data["parent_user"]),
            ("Teacher", data["teacher_user"]),
            ("Admin", data["admin"]),
        ]:
            notifs = Notification.objects.filter(
                recipient=user,
                notification_type=Notification.Type.ATTENDANCE,
            )
            self.stdout.write(f"  {role_name} ({user.username}) notifications: {notifs.count()}")
            for n in notifs:
                self.stdout.write(f"    - type={n.notification_type}, body_en={n.body_en}")

        return new_count

    # ─────────────────────────────────────────────────────────────────────────
    # Test 2: Low Grade Notification
    # ─────────────────────────────────────────────────────────────────────────

    @transaction.atomic
    def _test_low_grade_notification(self, data):
        """Test: creating a grade below 50% should create LOW_GRADE notifications."""
        self.stdout.write("\n=== Test 2: Low Grade Notification ===")
        student = data["student"]
        teacher = data["teacher"]
        subject = data["subject"]

        # Create an exam with total_grade=100
        exam, _ = Exam.objects.get_or_create(
            name="TESTNOTIF Math Exam",
            subject=subject,
            teacher=teacher,
            defaults={
                "total_grade": Decimal("100"),
                "duration": 60,
                "exam_type": Exam.QUIZ,
            },
        )
        self.stdout.write(f"  Exam: {exam.name} (total_grade={exam.total_grade})")

        # Remove any existing grade for this student/exam
        Grade.objects.filter(student=student, exam=exam).delete()

        before_count = Notification.objects.count()
        self.stdout.write(f"  Notifications before: {before_count}")

        # Create a grade with score=40/100 (40%) — below 50% threshold
        grade = Grade.objects.create(student=student, exam=exam, score=Decimal("40"))
        pct = grade.get_percentage()
        self.stdout.write(f"  Created grade: score={grade.score}/{exam.total_grade} = {pct:.1f}%")

        after_count = Notification.objects.count()
        new_count = after_count - before_count
        self.stdout.write(f"  Notifications after: {after_count}")
        self.stdout.write(f"  New notifications created: {new_count}")

        # Check each role
        for role_name, user in [
            ("Student", data["student_user"]),
            ("Parent", data["parent_user"]),
            ("Teacher", data["teacher_user"]),
            ("Admin", data["admin"]),
        ]:
            notifs = Notification.objects.filter(
                recipient=user,
                notification_type=Notification.Type.LOW_GRADE,
            )
            self.stdout.write(f"  {role_name} ({user.username}) notifications: {notifs.count()}")
            for n in notifs:
                self.stdout.write(f"    - type={n.notification_type}, body_en={n.body_en}")

        # ── Validation: 45/50 (90%) must NOT trigger ────────────────────────
        self.stdout.write("\n  === Validation: 45/50 (90%) must NOT trigger low-grade ===")
        exam2, _ = Exam.objects.get_or_create(
            name="TESTNOTIF Math Exam 50pt",
            subject=subject,
            teacher=teacher,
            defaults={
                "total_grade": Decimal("50"),
                "duration": 30,
                "exam_type": Exam.QUIZ,
            },
        )
        Grade.objects.filter(student=student, exam=exam2).delete()

        before_low = Notification.objects.filter(
            notification_type=Notification.Type.LOW_GRADE,
        ).count()

        grade2 = Grade.objects.create(student=student, exam=exam2, score=Decimal("45"))
        pct2 = grade2.get_percentage()
        self.stdout.write(f"  Created grade: score={grade2.score}/{exam2.total_grade} = {pct2:.1f}%")

        after_low = Notification.objects.filter(
            notification_type=Notification.Type.LOW_GRADE,
        ).count()
        new_low_grade = after_low - before_low
        self.stdout.write(f"  New LOW_GRADE notifications for 90% score: {new_low_grade}")
        if new_low_grade == 0:
            self.stdout.write(self.style.SUCCESS("  PASS: 45/50 (90%) did NOT trigger low-grade notification"))
        else:
            self.stdout.write(self.style.ERROR("  FAIL: 45/50 (90%) incorrectly triggered low-grade notification!"))

        return new_count

    # ─────────────────────────────────────────────────────────────────────────
    # Test 3: At-Risk Student Detection
    # ─────────────────────────────────────────────────────────────────────────

    @transaction.atomic
    def _test_at_risk_notification(self, data):
        """Test: at-risk detection should flag students with >=3 absences or avg<50%."""
        self.stdout.write("\n=== Test 3: At-Risk Student Detection ===")
        student = data["student"]
        today = date.today()

        # Create 3 absences within the recent window
        Attendance.objects.filter(student=student).delete()
        for i in range(3):
            att_date = today - timedelta(days=i)
            Attendance.objects.get_or_create(
                student=student,
                date=att_date,
                defaults={"status": Attendance.ABSENT},
            )
        absence_count = Attendance.objects.filter(
            student=student, status=Attendance.ABSENT
        ).count()
        self.stdout.write(f"  Created {absence_count} absences for student")

        before_count = Notification.objects.filter(
            notification_type=Notification.Type.AT_RISK,
        ).count()
        self.stdout.write(f"  AT_RISK notifications before: {before_count}")

        # Run at-risk detection
        count = run_at_risk_detection()
        self.stdout.write(f"  At-risk students detected: {count}")

        after_count = Notification.objects.filter(
            notification_type=Notification.Type.AT_RISK,
        ).count()
        new_count = after_count - before_count
        self.stdout.write(f"  New AT_RISK notifications: {new_count}")

        # Check each role (NOT student — at-risk doesn't notify student)
        for role_name, user in [
            ("Parent", data["parent_user"]),
            ("Teacher", data["teacher_user"]),
            ("Admin", data["admin"]),
        ]:
            notifs = Notification.objects.filter(
                recipient=user,
                notification_type=Notification.Type.AT_RISK,
            )
            self.stdout.write(f"  {role_name} ({user.username}) notifications: {notifs.count()}")
            for n in notifs:
                self.stdout.write(f"    - type={n.notification_type}, body_en={n.body_en}")

        # Verify student does NOT receive at-risk notification
        student_at_risk = Notification.objects.filter(
            recipient=data["student_user"],
            notification_type=Notification.Type.AT_RISK,
        ).count()
        self.stdout.write(f"  Student at-risk notifications: {student_at_risk}")
        if student_at_risk == 0:
            self.stdout.write(self.style.SUCCESS("  PASS: Student does NOT receive at-risk notification (correct)"))
        else:
            self.stdout.write(self.style.ERROR("  FAIL: Student incorrectly received at-risk notification!"))

        return new_count