from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReportViewSet, WeeklyReportViewSet

router = DefaultRouter()
router.register(r'reports', ReportViewSet, basename='report')
router.register(r'weekly-reports', WeeklyReportViewSet, basename='weekly-report')

urlpatterns = [
    path('', include(router.urls)),
]

