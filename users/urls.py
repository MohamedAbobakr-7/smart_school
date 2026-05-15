from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import UserViewSet
from .serializers import CustomTokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    # Authentication endpoints
    path('auth/login/', TokenObtainPairView.as_view(serializer_class=CustomTokenObtainPairSerializer), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # User endpoints
    path('', include(router.urls)),
]
