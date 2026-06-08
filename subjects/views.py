from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from users.permissions import IsAdmin, IsAdminOrTeacher
from .models import Subject, Material
from .serializers import SubjectSerializer, MaterialSerializer


class SubjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Subject management.
    - List/Retrieve: ADMIN, TEACHER (all subjects); STUDENT (only enrolled subjects)
    - Create/Update/Delete: ADMIN, TEACHER only
    - For STUDENT users, teacher_names/teachers_count are filtered to only show
      the teacher(s) assigned to the student's specific class via TeacherSubjectClass.
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

    def _get_student_class_teachers_map(self, student, subject_ids):
        """
        Build a mapping of subject_id -> list of teacher objects for a student's class.

        Strategy 1: Match via TeacherSubjectClass using all possible class identifiers
                    (student.class_id, school_class PK, school_class display name).
        Strategy 2: If no TSC records match, fall back to Teacher.assigned_classes
                    matching the student's school_class FK.
        """
        from teachers.models import Teacher, TeacherSubjectClass

        # Collect all possible class identifiers for this student
        class_ids = set()
        if student.class_id:
            class_ids.add(student.class_id)
        if student.school_class:
            class_ids.add(str(student.school_class.id))
            class_ids.add(str(student.school_class))

        # Strategy 1: TeacherSubjectClass lookup
        tsc_map = {}
        if class_ids and subject_ids:
            for tsc in TeacherSubjectClass.objects.filter(
                class_id__in=list(class_ids),
                subject_id__in=subject_ids,
            ).select_related('teacher', 'teacher__user'):
                tsc_map.setdefault(tsc.subject_id, []).append(tsc)

        # Strategy 2: If no TSC matches found, try Teacher.assigned_classes
        if not tsc_map and student.school_class and subject_ids:
            for subject_id in subject_ids:
                matching_teachers = list(
                    Teacher.objects.filter(
                        assigned_subjects__id=subject_id,
                        assigned_classes=student.school_class,
                    ).select_related('user')
                )
                if matching_teachers:
                    tsc_map[subject_id] = matching_teachers

        return tsc_map

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        # For student users: annotate each subject with class-specific teachers
        user = request.user
        if user.role == 'STUDENT' and hasattr(user, 'student_profile'):
            student = user.student_profile
            subject_ids = list(queryset.values_list('id', flat=True))

            tsc_map = self._get_student_class_teachers_map(student, subject_ids)

            # Evaluate queryset into a list so _class_teachers persists through pagination
            subject_list = list(queryset)
            for subject in subject_list:
                subject._class_teachers = tsc_map.get(subject.id, [])

            page = self.paginate_queryset(subject_list)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(subject_list, many=True)
            return Response(serializer.data)

        # Default flow for non-student users
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        subject = self.get_object()

        # For student users: annotate subject with class-specific teachers
        user = request.user
        if user.role == 'STUDENT' and hasattr(user, 'student_profile'):
            student = user.student_profile
            tsc_map = self._get_student_class_teachers_map(student, [subject.id])
            subject._class_teachers = tsc_map.get(subject.id, [])

        serializer = self.get_serializer(subject)
        return Response(serializer.data)

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
