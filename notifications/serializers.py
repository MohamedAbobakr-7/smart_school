from rest_framework import serializers

from .models import Notification, NotificationPreference


class NotificationSerializer(serializers.ModelSerializer):
    is_read = serializers.BooleanField(read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id",
            "notification_type",
            "title", "title_en", "title_ar",
            "body", "body_en", "body_ar",
            "metadata",
            "is_read",
            "read_at",
            "dedupe_key",
            "created_at",
        ]
        read_only_fields = fields


class NotificationPushSerializer(serializers.ModelSerializer):
    """Minimal payload for WebSocket delivery."""

    class Meta:
        model = Notification
        fields = ["id", "notification_type", "title", "title_en", "title_ar", "body", "body_en", "body_ar", "metadata", "created_at"]


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = [
            "allow_low_grade",
            "allow_attendance",
            "allow_student_report",
            "allow_weekly_report",
            "allow_exam_reminder",
            "updated_at",
        ]
        read_only_fields = ["updated_at"]
