from rest_framework.routers import DefaultRouter
from .views import SchoolClassViewSet

router = DefaultRouter()
router.register(r'classes', SchoolClassViewSet, basename='classes')

urlpatterns = router.urls
