from django.utils import timezone
from rest_framework import generics, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Notification, NotificationPreference
from .serializers import NotificationPreferenceSerializer, NotificationSerializer
from .services import get_or_create_preferences, mark_read


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """List and retrieve the current user's notifications."""

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Notification.objects.filter(recipient=self.request.user)
        unread = self.request.query_params.get("unread")
        if unread and unread.lower() in ("1", "true", "yes"):
            qs = qs.filter(read_at__isnull=True)
        ntype = self.request.query_params.get("type")
        if ntype:
            qs = qs.filter(notification_type=ntype)
        return qs

    @action(detail=True, methods=["post"], url_path="mark-read")
    def mark_read_action(self, request, pk=None):
        notification = self.get_object()
        mark_read(notification)
        return Response(NotificationSerializer(notification).data)

    @action(detail=False, methods=["post"], url_path="mark-all-read")
    def mark_all_read(self, request):
        n = (
            Notification.objects.filter(recipient=request.user, read_at__isnull=True).update(
                read_at=timezone.now()
            )
        )
        return Response({"marked_read": n})


class NotificationPreferenceView(generics.RetrieveUpdateAPIView):
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return get_or_create_preferences(self.request.user)
