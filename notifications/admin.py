from django.contrib import admin

from .models import Notification, NotificationPreference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "notification_type", "recipient", "title", "read_at", "created_at")
    list_filter = ("notification_type", "read_at")
    search_fields = ("title", "body", "recipient__username")
    raw_id_fields = ("recipient",)


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "allow_low_grade", "allow_attendance", "allow_student_report", "allow_weekly_report")
    raw_id_fields = ("user",)
