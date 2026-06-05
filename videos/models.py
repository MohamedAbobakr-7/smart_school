from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
import os


def educational_video_upload_to(instance, filename):
    return f"educational_videos/{instance.uploaded_by_id or 'pending'}/{filename}"


class Video(models.Model):
    """
    Teacher-uploaded educational video, organized by subject and category.
    """

    class Category(models.TextChoices):
        LECTURE = "lecture", _("Lecture")
        TUTORIAL = "tutorial", _("Tutorial")
        REVIEW = "review", _("Review")
        LAB = "lab", _("Lab / Demo")
        OTHER = "other", _("Other")

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    subject = models.ForeignKey(
        "subjects.Subject",
        on_delete=models.CASCADE,
        related_name="videos",
    )
    category = models.CharField(
        max_length=32,
        choices=Category.choices,
        default=Category.LECTURE,
        db_index=True,
    )
    uploaded_by = models.ForeignKey(
        "teachers.Teacher",
        on_delete=models.CASCADE,
        related_name="uploaded_videos",
    )
    target_classes = models.ManyToManyField(
        "classes.SchoolClass",
        related_name="videos",
        help_text="Target classes for this educational video.",
    )
    video_file = models.FileField(
        upload_to=educational_video_upload_to,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["mp4", "webm", "mov", "m4v", "ogg"]
            )
        ],
    )
    duration_seconds = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Optional; clients may send duration after upload for progress %",
    )
    is_published = models.BooleanField(default=True, db_index=True)
    display_order = models.PositiveSmallIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "educational_videos"
        ordering = ["subject", "display_order", "-created_at"]
        indexes = [
            models.Index(fields=["subject", "is_published", "category"]),
            models.Index(fields=["uploaded_by", "is_published"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.subject.code})"


@receiver(post_delete, sender=Video)
def auto_delete_video_on_delete(sender, instance, **kwargs):
    """
    Deletes video file from filesystem
    when corresponding `Video` object is deleted.
    """
    if instance.video_file:
        if os.path.isfile(instance.video_file.path):
            os.remove(instance.video_file.path)


class VideoProgress(models.Model):
    """
    Per-student watch time, resume position, and completion for a video.
    """

    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="video_progress",
    )
    video = models.ForeignKey(
        Video,
        on_delete=models.CASCADE,
        related_name="progress_records",
    )
    last_position_seconds = models.PositiveIntegerField(
        default=0,
        help_text="Last playback position for resume",
    )
    total_watch_seconds = models.PositiveIntegerField(
        default=0,
        help_text="Cumulative engaged watch time reported by the client",
    )
    is_completed = models.BooleanField(default=False, db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "video_progress"
        constraints = [
            models.UniqueConstraint(
                fields=["student", "video"],
                name="uniq_video_progress_student_video",
            ),
        ]
        indexes = [
            models.Index(fields=["student", "updated_at"]),
            models.Index(fields=["video", "is_completed"]),
        ]

    def __str__(self):
        return f"{self.student.student_id} — {self.video_id}"
