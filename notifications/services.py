"""
Create notifications, respect user preferences, and push over Channels.
"""
from __future__ import annotations

from typing import Any

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import Notification, NotificationPreference

User = get_user_model()


def get_or_create_preferences(user) -> NotificationPreference:
    prefs, _ = NotificationPreference.objects.get_or_create(user=user)
    return prefs


def is_allowed(user, notification_type: str) -> bool:
    prefs = get_or_create_preferences(user)
    if notification_type == Notification.Type.LOW_GRADE:
        return prefs.allow_low_grade
    if notification_type == Notification.Type.ATTENDANCE:
        return prefs.allow_attendance
    if notification_type == Notification.Type.NEW_STUDENT_REPORT:
        return prefs.allow_student_report
    if notification_type == Notification.Type.NEW_WEEKLY_REPORT:
        return prefs.allow_weekly_report
    if notification_type == Notification.Type.EXAM_REMINDER:
        return prefs.allow_exam_reminder
    return True


def create_notification(
    *,
    recipient,
    notification_type: str,
    title: str = "",
    body: str = "",
    title_en: str = "",
    title_ar: str = "",
    body_en: str = "",
    body_ar: str = "",
    metadata: dict[str, Any] | None = None,
    dedupe_key: str = "",
    broadcast: bool = True,
) -> Notification | None:
    if not recipient or not recipient.is_authenticated:
        return None
    if not is_allowed(recipient, notification_type):
        return None

    meta = metadata or {}
    # Use explicit localized fields; fall back to title/body for both languages
    t_en = title_en or title
    t_ar = title_ar or title
    b_en = body_en or body
    b_ar = body_ar or body

    kwargs = {
        "recipient": recipient,
        "notification_type": notification_type,
        "title": t_en[:200],          # base field (required by DB); use English as default
        "title_en": t_en[:200],
        "title_ar": t_ar[:200],
        "body": b_en,                 # base field (required by DB); use English as default
        "body_en": b_en,
        "body_ar": b_ar,
        "metadata": meta,
    }
    if dedupe_key:
        existing = Notification.objects.filter(
            recipient=recipient,
            dedupe_key=dedupe_key,
        ).first()
        if existing:
            return existing
        kwargs["dedupe_key"] = dedupe_key

    n = Notification.objects.create(**kwargs)
    if broadcast:
        push_to_websocket(n)
    return n


def mark_read(notification: Notification) -> None:
    if notification.read_at is None:
        notification.read_at = timezone.now()
        notification.save(update_fields=["read_at"])


def push_to_websocket(notification: Notification) -> None:
    layer = get_channel_layer()
    if layer is None:
        return
    from .serializers import NotificationPushSerializer

    payload = NotificationPushSerializer(notification).data
    async_to_sync(layer.group_send)(
        f"notifications_user_{notification.recipient_id}",
        {"type": "push_notification", "payload": payload},
    )
