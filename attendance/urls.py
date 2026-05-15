from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AttendanceViewSet, AttendanceSessionViewSet

router = DefaultRouter()
router.register(r'attendance', AttendanceViewSet, basename='attendance')
router.register(r'attendance-sessions', AttendanceSessionViewSet, basename='attendance-session')

urlpatterns = [
    path('', include(router.urls)),
]

