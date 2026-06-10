from django.utils import timezone
from rest_framework import generics, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Notification, NotificationPreference
from .serializers import NotificationPreferenceSerializer, NotificationSerializer
from .services import get_or_create_preferences, mark_read, mark_all_read, get_unread_count


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List and retrieve the current user's notifications.

    Role-based visibility is enforced at the **delivery** level via signals:
    each role only receives notifications that are relevant to them, so the
    queryset simply filters by recipient.  Additional query params allow
    filtering by type and unread status.
    """

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Notification.objects.filter(recipient=user).select_related(
            "student__user", "student__school_class"
        )

        # ── Filter by unread status ──────────────────────────────────────────
        unread = self.request.query_params.get("unread")
        if unread and unread.lower() in ("1", "true", "yes"):
            qs = qs.filter(read_at__isnull=True)

        # ── Filter by notification type ──────────────────────────────────────
        ntype = self.request.query_params.get("type")
        if ntype:
            qs = qs.filter(notification_type=ntype)

        # ── Filter by student (for parents/teachers viewing a specific child) ─
        student_id = self.request.query_params.get("student_id")
        if student_id:
            qs = qs.filter(student__student_id=student_id)

        return qs

    @action(detail=True, methods=["post"], url_path="mark-read")
    def mark_read_action(self, request, pk=None):
        notification = self.get_object()
        mark_read(notification)
        return Response(NotificationSerializer(notification).data)

    @action(detail=False, methods=["post"], url_path="mark-all-read")
    def mark_all_read_action(self, request):
        n = mark_all_read(request.user)
        return Response({"marked_read": n})

    @action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count_action(self, request):
        count = get_unread_count(request.user)
        return Response({"unread_count": count})


class NotificationPreferenceView(generics.RetrieveUpdateAPIView):
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return get_or_create_preferences(self.request.user)
