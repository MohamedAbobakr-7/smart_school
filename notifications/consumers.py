from channels.generic.websocket import AsyncJsonWebsocketConsumer


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """
    Real-time delivery: join group notifications_user_<id>.
    Connect with: ws://host/ws/notifications/?access=<JWT>
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
        await self.send_json(event["payload"])
