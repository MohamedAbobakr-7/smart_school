from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ExamViewSet, GradeViewSet

router = DefaultRouter()
router.register(r'exams', ExamViewSet, basename='exam')
router.register(r'grades', GradeViewSet, basename='grade')

urlpatterns = [
    path('', include(router.urls)),
]

