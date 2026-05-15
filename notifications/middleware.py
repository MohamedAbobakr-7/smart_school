from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken


@database_sync_to_async
def _user_from_jwt(token: str):
    from django.contrib.auth import get_user_model

    User = get_user_model()
    try:
        access = AccessToken(token)
        uid = access["user_id"]
        return User.objects.get(pk=uid)
    except (User.DoesNotExist, TokenError, InvalidToken, KeyError):
        return AnonymousUser()


class JWTWebSocketMiddleware:
    """Authenticate WebSocket connections via ?access=<jwt>."""

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        if scope["type"] == "websocket":
            qs = parse_qs(scope.get("query_string", b"").decode())
            token = (qs.get("access") or [None])[0]
            if token:
                scope["user"] = await _user_from_jwt(token)
            else:
                scope["user"] = AnonymousUser()
        return await self.inner(scope, receive, send)
