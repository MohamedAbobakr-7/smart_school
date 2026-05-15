from rest_framework import serializers

from subjects.serializers import SubjectSerializer
from teachers.models import Teacher

from .models import Video, VideoProgress


class VideoSerializer(serializers.ModelSerializer):
    subject_detail = SubjectSerializer(source="subject", read_only=True)
    stream_url_template = serializers.SerializerMethodField(read_only=True)
    uploaded_by = serializers.PrimaryKeyRelatedField(
        queryset=Teacher.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Video
        fields = [
            "id",
            "title",
            "description",
            "subject",
            "subject_detail",
            "category",
            "uploaded_by",
            "video_file",
            "duration_seconds",
            "is_published",
            "display_order",
            "created_at",
            "updated_at",
            "stream_url_template",
        ]
        read_only_fields = ["created_at", "updated_at", "stream_url_template"]

    def get_stream_url_template(self, obj):
        request = self.context.get("request")
        if not request:
            return None
        path = f"/api/videos/{obj.pk}/stream/"
        return request.build_absolute_uri(path) + "?access=<JWT>"

    def validate(self, attrs):
        request = self.context.get("request")
        if request and request.user.is_teacher():
            attrs.pop("uploaded_by", None)
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        user = request.user
        if user.is_teacher() and hasattr(user, "teacher_profile"):
            validated_data["uploaded_by"] = user.teacher_profile
        elif user.is_admin():
            if not validated_data.get("uploaded_by"):
                raise serializers.ValidationError(
                    {"uploaded_by": "Administrators must set uploaded_by (teacher id)."}
                )
        else:
            raise serializers.ValidationError("Only teachers and admins can upload videos.")
        return super().create(validated_data)


class VideoListSerializer(serializers.ModelSerializer):
    """Lightweight list for library views."""

    subject_code = serializers.CharField(source="subject.code", read_only=True)
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    uploaded_by_name = serializers.SerializerMethodField()
    stream_url_template = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Video
        fields = [
            "id",
            "title",
            "description",
            "subject",
            "subject_code",
            "subject_name",
            "category",
            "uploaded_by",
            "uploaded_by_name",
            "duration_seconds",
            "is_published",
            "display_order",
            "created_at",
            "stream_url_template",
        ]

    def get_uploaded_by_name(self, obj):
        u = obj.uploaded_by.user
        return u.get_full_name() or u.username

    def get_stream_url_template(self, obj):
        request = self.context.get("request")
        if not request:
            return None
        return request.build_absolute_uri(f"/api/videos/{obj.pk}/stream/") + "?access=<JWT>"


class VideoProgressSerializer(serializers.ModelSerializer):
    video_title = serializers.CharField(source="video.title", read_only=True)
    subject_name = serializers.CharField(source="video.subject.name", read_only=True)

    class Meta:
        model = VideoProgress
        fields = [
            "id",
            "student",
            "video",
            "video_title",
            "subject_name",
            "last_position_seconds",
            "total_watch_seconds",
            "is_completed",
            "completed_at",
            "updated_at",
        ]
        read_only_fields = [
            "student",
            "video",
            "video_title",
            "subject_name",
            "last_position_seconds",
            "total_watch_seconds",
            "is_completed",
            "completed_at",
            "updated_at",
        ]


class VideoProgressSyncSerializer(serializers.Serializer):
    video = serializers.PrimaryKeyRelatedField(queryset=Video.objects.all())
    last_position_seconds = serializers.IntegerField(min_value=0)
    extra_watch_seconds = serializers.IntegerField(min_value=0, max_value=7200, default=0)
    video_duration_seconds = serializers.IntegerField(
        min_value=0, required=False, allow_null=True
    )
    mark_completed = serializers.BooleanField(default=False)

    def validate_video(self, video):
        request = self.context["request"]
        if not video.is_published and not (
            request.user.is_admin()
            or (
                request.user.is_teacher()
                and hasattr(request.user, "teacher_profile")
                and video.uploaded_by_id == request.user.teacher_profile.id
            )
        ):
            raise serializers.ValidationError("Video is not available.")
        return video
