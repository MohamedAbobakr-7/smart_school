from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from users.permissions import IsAdmin, IsAdminOrTeacher
from .models import SchoolClass
from .serializers import SchoolClassSerializer


class SchoolClassViewSet(viewsets.ModelViewSet):
    """
    ViewSet for SchoolClass management.
    - List/Retrieve: any authenticated user
    - Create/Update/Delete: ADMIN only
    - my_classes=true: teachers see only their assigned classes
    """
    queryset = SchoolClass.objects.all()
    serializer_class = SchoolClassSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'section', 'description']
    ordering_fields = ['name', 'section', 'created_at']

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        if self.request.query_params.get('my_classes') == 'true':
            if hasattr(user, 'teacher_profile'):
                teacher = user.teacher_profile
                qs = qs.filter(teachers=teacher)

        return qs

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        return [IsAuthenticated()]
