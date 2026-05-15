import os

from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.permissions import IsAdmin, IsAdminOrTeacher

from .authentication import JWTAccessQueryAuthentication
from .models import Video, VideoProgress
from .serializers import (
    VideoListSerializer,
    VideoProgressSerializer,
    VideoProgressSyncSerializer,
    VideoSerializer,
)
from .streaming import file_streaming_response


def _video_content_type(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower().lstrip(".")
    return {
        "mp4": "video/mp4",
        "webm": "video/webm",
        "mov": "video/quicktime",
        "m4v": "video/x-m4v",
        "ogg": "video/ogg",
    }.get(ext, "application/octet-stream")


class VideoViewSet(viewsets.ModelViewSet):
    """
    Teachers/admins upload and manage videos; students see published catalog.
    Stream with Range support: GET .../videos/:id/stream/?access=<JWT>
    """

    permission_classes = [IsAuthenticated]
    queryset = Video.objects.select_related("subject", "uploaded_by", "uploaded_by__user")

    def get_serializer_class(self):
        if self.action == "list":
            return VideoListSerializer
        return VideoSerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAdminOrTeacher()]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        subject = self.request.query_params.get("subject")
        category = self.request.query_params.get("category")
        if subject:
            qs = qs.filter(subject_id=subject)
        if category:
            qs = qs.filter(category=category)

        if user.is_admin():
            return qs
        if user.is_teacher() and hasattr(user, "teacher_profile"):
            tp = user.teacher_profile
            return qs.filter(Q(is_published=True) | Q(uploaded_by=tp))
        if user.is_student():
            return qs.filter(is_published=True)
        return Video.objects.none()

    def perform_update(self, serializer):
        user = self.request.user
        if user.is_teacher() and hasattr(user, "teacher_profile"):
            if serializer.instance.uploaded_by_id != user.teacher_profile.id:
                raise PermissionDenied("You can only edit your own videos.")
        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        if user.is_teacher() and hasattr(user, "teacher_profile"):
            if instance.uploaded_by_id != user.teacher_profile.id:
                raise PermissionDenied("You can only delete your own videos.")
        instance.delete()

    @action(
        detail=True,
        methods=["get"],
        url_path="stream",
        authentication_classes=[JWTAccessQueryAuthentication],
        permission_classes=[IsAuthenticated],
    )
    def stream(self, request, pk=None):
        video = self.get_object()
        if not video.video_file:
            return Response({"detail": "No file."}, status=status.HTTP_404_NOT_FOUND)
        path = video.video_file.path
        if not os.path.isfile(path):
            return Response({"detail": "File missing."}, status=status.HTTP_404_NOT_FOUND)
        return file_streaming_response(path, request, content_type=_video_content_type(path))


class VideoProgressViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Students: own progress. Teachers: progress for videos they uploaded (optional ?video=).
    """

    serializer_class = VideoProgressSerializer
    permission_classes = [IsAuthenticated]
    queryset = VideoProgress.objects.select_related("video", "video__subject", "student", "student__user")

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if user.is_student() and hasattr(user, "student_profile"):
            qs = qs.filter(student=user.student_profile)
        elif user.is_teacher() and hasattr(user, "teacher_profile"):
            qs = qs.filter(video__uploaded_by=user.teacher_profile)
            vid = self.request.query_params.get("video")
            if vid:
                qs = qs.filter(video_id=vid)
        elif user.is_admin():
            vid = self.request.query_params.get("video")
            if vid:
                qs = qs.filter(video_id=vid)
        else:
            return VideoProgress.objects.none()
        return qs.order_by("-updated_at")

    @action(detail=False, methods=["post"], url_path="sync")
    def sync(self, request):
        if not request.user.is_student() or not hasattr(request.user, "student_profile"):
            return Response(
                {"detail": "Only students can sync watch progress."},
                status=status.HTTP_403_FORBIDDEN,
            )
        ser = VideoProgressSyncSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        from django.utils import timezone

        student = request.user.student_profile
        video = ser.validated_data["video"]
        pos = ser.validated_data["last_position_seconds"]
        extra = ser.validated_data.get("extra_watch_seconds") or 0
        duration = ser.validated_data.get("video_duration_seconds")
        mark_completed = ser.validated_data.get("mark_completed") or False

        progress, _created = VideoProgress.objects.get_or_create(
            student=student,
            video=video,
            defaults={
                "last_position_seconds": 0,
                "total_watch_seconds": 0,
            },
        )

        progress.last_position_seconds = max(progress.last_position_seconds, pos)
        progress.total_watch_seconds += extra

        if duration and not video.duration_seconds:
            video.duration_seconds = duration
            video.save(update_fields=["duration_seconds", "updated_at"])

        eff_duration = duration or video.duration_seconds
        if mark_completed or (
            eff_duration
            and eff_duration > 0
            and progress.last_position_seconds >= eff_duration * 92 // 100
        ):
            progress.is_completed = True
            if not progress.completed_at:
                progress.completed_at = timezone.now()

        progress.save()
        return Response(VideoProgressSerializer(progress, context={"request": request}).data)
