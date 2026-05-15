from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import NotificationPreferenceView, NotificationViewSet

router = DefaultRouter()
router.register(r"notifications", NotificationViewSet, basename="notification")

urlpatterns = [
    path("", include(router.urls)),
    path("notification-preferences/", NotificationPreferenceView.as_view(), name="notification-preferences"),
]
