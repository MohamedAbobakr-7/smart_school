from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import VideoProgressViewSet, VideoViewSet

router = DefaultRouter()
router.register(r"videos", VideoViewSet, basename="video")
router.register(r"video-progress", VideoProgressViewSet, basename="video-progress")

urlpatterns = [
    path("", include(router.urls)),
]
