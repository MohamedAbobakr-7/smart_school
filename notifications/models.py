from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Notification(models.Model):
    """In-app notification with typed payload for smart school alerts."""

    class Type(models.TextChoices):
        LOW_GRADE = "LOW_GRADE", _("Low Grade")
        ATTENDANCE = "ATTENDANCE", _("Attendance")
        EXAM_REMINDER = "EXAM_REMINDER", _("Exam Reminder")
        NEW_STUDENT_REPORT = "NEW_STUDENT_REPORT", _("New Student Report")
        NEW_WEEKLY_REPORT = "NEW_WEEKLY_REPORT", _("New Weekly Report")
        SYSTEM = "SYSTEM", _("System")

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    notification_type = models.CharField(
        max_length=32,
        choices=Type.choices,
        db_index=True,
    )
    title = models.CharField(max_length=200)
    body = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    dedupe_key = models.CharField(
        max_length=160,
        blank=True,
        db_index=True,
        help_text="Optional key to avoid duplicate alerts (e.g. same absence day).",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "-created_at"]),
            models.Index(fields=["recipient", "read_at"]),
        ]

    def __str__(self):
        return f"{self.notification_type} → {self.recipient_id}"

    @property
    def is_read(self):
        return self.read_at is not None


class NotificationPreference(models.Model):
    """Per-user toggles for automated notification categories."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_preferences",
    )
    allow_low_grade = models.BooleanField(default=True)
    allow_attendance = models.BooleanField(default=True)
    allow_student_report = models.BooleanField(default=True)
    allow_weekly_report = models.BooleanField(default=True)
    allow_exam_reminder = models.BooleanField(default=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "notification_preferences"

    def __str__(self):
        return f"prefs:{self.user_id}"
