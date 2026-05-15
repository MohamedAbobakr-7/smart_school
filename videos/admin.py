from django.contrib import admin

from .models import Video, VideoProgress


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "subject",
        "category",
        "uploaded_by",
        "is_published",
        "duration_seconds",
        "created_at",
    )
    list_filter = ("is_published", "category", "subject")
    search_fields = ("title", "description")


@admin.register(VideoProgress)
class VideoProgressAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "video",
        "last_position_seconds",
        "total_watch_seconds",
        "is_completed",
        "updated_at",
    )
    list_filter = ("is_completed",)
    search_fields = ("student__student_id", "video__title")
