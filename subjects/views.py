from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from users.permissions import IsAdmin, IsAdminOrTeacher
from .models import Subject, Material
from .serializers import SubjectSerializer, MaterialSerializer


class SubjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Subject management.
    - List/Retrieve: ADMIN, TEACHER (all subjects); STUDENT (only enrolled subjects)
    - Create/Update/Delete: ADMIN, TEACHER only
    """
    serializer_class = SubjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Subject.objects.all()
        user = self.request.user

        if self.request.query_params.get('my_subjects') == 'true':
            if hasattr(user, 'teacher_profile'):
                teacher = user.teacher_profile
                qs = qs.filter(teachers=teacher)
            elif hasattr(user, 'student_profile'):
                student = user.student_profile
                qs = qs.filter(enrolled_students=student)

        # Students can only see their enrolled subjects
        if user.role == 'STUDENT' and hasattr(user, 'student_profile'):
            student = user.student_profile
            qs = qs.filter(enrolled_students=student)

        return qs

    def get_permissions(self):
        """Override permissions based on action"""
        if self.action in ['create', 'destroy', 'update', 'partial_update']:
            # Only ADMIN and TEACHER can create, update, or delete
            return [IsAdminOrTeacher()]
        elif self.action in ['list', 'retrieve']:
            # ADMIN, TEACHER, and STUDENT can view (students see only their subjects via get_queryset)
            return [IsAuthenticated()]
        return super().get_permissions()


class MaterialViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Material management.
    - List/Retrieve: Authenticated users (Students see materials for their subjects, Teachers see theirs)
    - Create/Update/Delete: ADMIN, TEACHER only
    """
    serializer_class = MaterialSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Material.objects.all().select_related('subject', 'uploaded_by', 'uploaded_by__user')
        
        # Filter by role
        if user.role == 'STUDENT' and hasattr(user, 'student_profile'):
            student = user.student_profile
            # Students can only see materials for subjects they are enrolled in
            enrolled_subject_ids = student.subjects.values_list('id', flat=True)
            qs = qs.filter(subject_id__in=enrolled_subject_ids)
            
        elif user.role == 'TEACHER' and hasattr(user, 'teacher_profile'):
            teacher = user.teacher_profile
            # Teachers can see materials for subjects they teach
            teacher_subject_ids = teacher.assigned_subjects.values_list('id', flat=True)
            qs = qs.filter(subject_id__in=teacher_subject_ids)
            
        elif user.role == 'PARENT' and hasattr(user, 'parent_profile'):
            # Parents can see materials for their children's subjects
            parent = user.parent_profile
            child_subject_ids = parent.children.values_list('subjects__id', flat=True)
            qs = qs.filter(subject_id__in=child_subject_ids)
            
        return qs.distinct()

    def get_permissions(self):
        if self.action in ['create', 'destroy', 'update', 'partial_update']:
            return [IsAdminOrTeacher()]
        return super().get_permissions()

    def perform_create(self, serializer):
        # Automatically set uploaded_by to the current teacher
        user = self.request.user
        if hasattr(user, 'teacher_profile'):
            serializer.save(uploaded_by=user.teacher_profile)
        else:
            serializer.save()

