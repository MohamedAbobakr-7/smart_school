from datetime import date

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from users.permissions import IsAdmin, IsAdminOrTeacher, IsStudent, IsParent
from .models import Exam, Question, Grade
from .serializers import (
    ExamSerializer, ExamDetailSerializer,
    QuestionSerializer, GradeSerializer
)


class ExamViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Exam management.
    - List/Retrieve: ADMIN, TEACHER (all), STUDENT/PARENT (exams they have grades for)
    - Create/Update/Delete: ADMIN, TEACHER only
    - upcoming: STUDENT can see exams for their subjects that they haven't taken yet
    """
    queryset = Exam.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Use detailed serializer for retrieve action"""
        if self.action == 'retrieve':
            return ExamDetailSerializer
        if self.action == 'upcoming':
            return ExamSerializer
        return ExamSerializer

    def get_permissions(self):
        """Override permissions based on action"""
        if self.action in ['create', 'destroy', 'update', 'partial_update']:
            # Only ADMIN and TEACHER can create, update, or delete
            return [IsAdminOrTeacher()]
        elif self.action in ['list', 'retrieve', 'upcoming']:
            # Authenticated users can view (filtered by role in get_queryset)
            return [IsAuthenticated()]
        return super().get_permissions()

    def get_queryset(self):
        """Filter queryset based on user role"""
        user = self.request.user
        
        if user.is_admin() or user.is_teacher():
            # ADMIN and TEACHER can see all exams
            return Exam.objects.all()
        elif user.is_student():
            # STUDENT can see exams they have grades for
            if hasattr(user, 'student_profile'):
                exam_ids = Grade.objects.filter(student=user.student_profile).values_list('exam_id', flat=True)
                return Exam.objects.filter(id__in=exam_ids)
            return Exam.objects.none()
        elif user.is_parent():
            # PARENT can see exams their children have grades for
            if hasattr(user, 'parent_profile'):
                children = user.parent_profile.children.all()
                exam_ids = Grade.objects.filter(student__in=children).values_list('exam_id', flat=True)
                return Exam.objects.filter(id__in=exam_ids)
            return Exam.objects.none()
        
        return Exam.objects.none()

    @action(detail=False, methods=['get'], url_path='upcoming', url_name='upcoming')
    def upcoming(self, request):
        """
        GET /api/exams/upcoming/

        Returns exams for the logged-in student's enrolled subjects
        that they haven't taken yet (no Grade record exists).
        Only exams with exam_date >= today or no exam_date are included,
        sorted by exam_date ascending.
        """
        user = request.user

        if not user.is_student():
            return Response([])

        student = getattr(user, 'student_profile', None)
        if student is None:
            return Response([])

        # Get subject IDs the student is enrolled in
        enrolled_subject_ids = student.subjects.values_list('id', flat=True)

        # Get exam IDs the student has already taken (has a Grade)
        taken_exam_ids = Grade.objects.filter(student=student).values_list('exam_id', flat=True)

        # Upcoming exams: in enrolled subjects, not yet taken, date >= today or no date
        today = date.today()
        upcoming_exams = (
            Exam.objects
            .filter(subject_id__in=enrolled_subject_ids)
            .exclude(id__in=taken_exam_ids)
            .filter(exam_date__gte=today) | Exam.objects
            .filter(subject_id__in=enrolled_subject_ids)
            .exclude(id__in=taken_exam_ids)
            .filter(exam_date__isnull=True)
        )
        upcoming_exams = upcoming_exams.order_by('exam_date', 'name')

        serializer = ExamSerializer(upcoming_exams, many=True, context={'request': request})
        return Response(serializer.data)


class QuestionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Question management.
    - List/Retrieve: ADMIN, TEACHER (all), STUDENT (questions for their exams)
    - Create/Update/Delete: ADMIN, TEACHER only
    """
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """Override permissions based on action"""
        if self.action in ['create', 'destroy', 'update', 'partial_update']:
            # Only ADMIN and TEACHER can create, update, or delete
            return [IsAdminOrTeacher()]
        elif self.action in ['list', 'retrieve']:
            # Authenticated users can view (filtered by role in get_queryset)
            return [IsAuthenticated()]
        return super().get_permissions()

    def get_queryset(self):
        """Filter queryset based on user role"""
        user = self.request.user
        
        if user.is_admin() or user.is_teacher():
            # ADMIN and TEACHER can see all questions
            return Question.objects.all()
        elif user.is_student():
            # STUDENT can see questions for exams they have grades for
            if hasattr(user, 'student_profile'):
                exam_ids = Grade.objects.filter(student=user.student_profile).values_list('exam_id', flat=True)
                return Question.objects.filter(exam_id__in=exam_ids)
            return Question.objects.none()
        
        return Question.objects.none()


class GradeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Grade management.
    - List/Retrieve: ADMIN, TEACHER (all), PARENT (own children), STUDENT (own)
    - Create/Update/Delete: ADMIN, TEACHER only
    """
    queryset = Grade.objects.all()
    serializer_class = GradeSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """Override permissions based on action"""
        if self.action in ['create', 'destroy', 'update', 'partial_update']:
            # Only ADMIN and TEACHER can create, update, or delete
            return [IsAdminOrTeacher()]
        elif self.action in ['list', 'retrieve']:
            # Authenticated users can view (filtered by role in get_queryset)
            return [IsAuthenticated()]
        return super().get_permissions()

    def get_queryset(self):
        """Filter queryset based on user role"""
        user = self.request.user
        
        if user.is_admin() or user.is_teacher():
            # ADMIN and TEACHER can see all grades
            return Grade.objects.all()
        elif user.is_student():
            # STUDENT can only see their own grades
            if hasattr(user, 'student_profile'):
                return Grade.objects.filter(student=user.student_profile)
            return Grade.objects.none()
        elif user.is_parent():
            # PARENT can see their children's grades
            if hasattr(user, 'parent_profile'):
                children = user.parent_profile.children.all()
                return Grade.objects.filter(student__in=children)
            return Grade.objects.none()
        
        return Grade.objects.none()

