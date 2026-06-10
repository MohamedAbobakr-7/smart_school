from rest_framework import serializers

from .models import Notification, NotificationPreference


class NotificationSerializer(serializers.ModelSerializer):
    is_read = serializers.BooleanField(read_only=True)
    student_name = serializers.SerializerMethodField()
    student_class = serializers.SerializerMethodField()

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
            "student",
            "student_name",
            "student_class",
            "created_at",
        ]
        read_only_fields = fields

    def get_student_name(self, obj):
        if obj.student:
            return obj.student.user.get_full_name() or obj.student.student_id or str(obj.student.pk)
        return None

    def get_student_class(self, obj):
        if obj.student and obj.student.school_class:
            return obj.student.school_class.display_name
        return None


class NotificationPushSerializer(serializers.ModelSerializer):
    """Minimal payload for WebSocket delivery."""

    student_name = serializers.SerializerMethodField()
    student_class = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id",
            "notification_type",
            "title", "title_en", "title_ar",
            "body", "body_en", "body_ar",
            "metadata",
            "student",
            "student_name",
            "student_class",
            "created_at",
        ]

    def get_student_name(self, obj):
        if obj.student:
            return obj.student.user.get_full_name() or obj.student.student_id or str(obj.student.pk)
        return None

    def get_student_class(self, obj):
        if obj.student and obj.student.school_class:
            return obj.student.school_class.display_name
        return None


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = [
            "allow_attendance",
            "allow_low_grade",
            "allow_at_risk",
            "allow_exam_reminder",
            "allow_student_report",
            "allow_weekly_report",
            "allow_system",
            "updated_at",
        ]
        read_only_fields = ["updated_at"]
