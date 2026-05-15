from django.db import models
from django.core.exceptions import ValidationError
from django.db.models.signals import post_delete
from django.dispatch import receiver
import os


class Report(models.Model):
    REPORT_TYPES = [
        ('academic', 'Academic'),
        ('behavioral', 'Behavioral'),
        ('attendance', 'Attendance'),
        ('general', 'General'),
    ]

    title = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES, default='general')
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='reports')
    content = models.TextField()
    generated_by = models.ForeignKey('teachers.Teacher', on_delete=models.SET_NULL, null=True, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'reports'
        verbose_name = 'Report'
        verbose_name_plural = 'Reports'
        ordering = ['-generated_at']

    def __str__(self):
        return f"{self.title} - {self.student.student_id}"


class WeeklyReport(models.Model):
    """
    Snapshot of school-wide or teacher-scoped analytics for a calendar week.
    Populated by the analytics service and optional PDF export.
    """

    class Scope(models.TextChoices):
        SCHOOL = "SCHOOL", "School"
        TEACHER = "TEACHER", "Teacher"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        READY = "READY", "Ready"
        FAILED = "FAILED", "Failed"

    week_start = models.DateField(help_text="First day of the reporting week (inclusive)")
    week_end = models.DateField(help_text="Last day of the reporting week (inclusive)")
    scope = models.CharField(max_length=10, choices=Scope.choices, db_index=True)
    teacher = models.ForeignKey(
        "teachers.Teacher",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="weekly_reports",
        help_text="Set when scope is TEACHER; null for school-wide",
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    dedupe_key = models.CharField(max_length=96, unique=True, editable=False)

    attendance_stats = models.JSONField(default=dict, blank=True)
    academic_stats = models.JSONField(default=dict, blank=True)
    exam_stats = models.JSONField(default=dict, blank=True)
    charts_payload = models.JSONField(default=dict, blank=True)
    insights = models.JSONField(default=list, blank=True)
    comparison_prior_week = models.JSONField(
        null=True,
        blank=True,
        help_text="Delta vs the immediately preceding week of equal length",
    )

    error_message = models.TextField(blank=True)
    pdf_file = models.FileField(upload_to="weekly_reports/pdf/", blank=True, null=True)

    generated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "weekly_reports"
        verbose_name = "Weekly Report"
        verbose_name_plural = "Weekly Reports"
        ordering = ["-week_start", "scope"]
        indexes = [
            models.Index(fields=["week_start", "scope"]),
            models.Index(fields=["teacher", "week_start"]),
        ]

    def __str__(self):
        who = "School" if self.scope == self.Scope.SCHOOL else (self.teacher_id or "Teacher")
        return f"Week {self.week_start} ({self.scope}) — {who}"

    def clean(self):
        super().clean()
        if self.scope == self.Scope.TEACHER and not self.teacher_id:
            raise ValidationError("Teacher is required when scope is TEACHER.")
        if self.scope == self.Scope.SCHOOL and self.teacher_id:
            raise ValidationError("Teacher must be empty when scope is SCHOOL.")
        if self.week_end and self.week_start and self.week_end < self.week_start:
            raise ValidationError("week_end cannot be before week_start.")

    def save(self, *args, **kwargs):
        if self.scope == self.Scope.SCHOOL:
            self.dedupe_key = f"{self.week_start.isoformat()}_SCHOOL"
        else:
            tid = self.teacher_id or 0
            self.dedupe_key = f"{self.week_start.isoformat()}_TEACHER_{tid}"
        self.full_clean()
        super().save(*args, **kwargs)


@receiver(post_delete, sender=WeeklyReport)
def auto_delete_pdf_on_delete(sender, instance, **kwargs):
    """
    Deletes PDF file from filesystem
    when corresponding `WeeklyReport` object is deleted.
    """
    if instance.pdf_file:
        if os.path.isfile(instance.pdf_file.path):
            os.remove(instance.pdf_file.path)
