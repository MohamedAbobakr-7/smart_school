from channels.generic.websocket import AsyncJsonWebsocketConsumer


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """
    Real-time delivery: join group notifications_user_<id>.
    Connect with: ws://host/ws/notifications/?access=<JWT>

    Handles two message types from the server:
      - push_notification: delivers a new notification payload
      - push_unread_count: delivers the updated unread count for badge updates
    """

    async def connect(self):
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close(code=4001)
            return
        self._group = f"notifications_user_{user.id}"
        await self.channel_layer.group_add(self._group, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, "_group"):
            await self.channel_layer.group_discard(self._group, self.channel_name)

    async def push_notification(self, event):
        """Handle push_notification events from the channel layer."""
        await self.send_json(event["payload"])

    async def push_unread_count(self, event):
        """Handle push_unread_count events — sends badge counter to frontend."""
        await self.send_json({
            "type": "unread_count",
            "unread_count": event["unread_count"],
        })
