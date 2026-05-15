"""
ASGI config for smartSchool (HTTP + WebSocket notifications).
"""
import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

from notifications.middleware import JWTWebSocketMiddleware
from notifications.routing import websocket_urlpatterns

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartSchool.settings')

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter(
    {
        'http': django_asgi_app,
        'websocket': JWTWebSocketMiddleware(URLRouter(websocket_urlpatterns)),
    }
)
