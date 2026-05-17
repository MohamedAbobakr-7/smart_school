from datetime import date, timedelta

from django.db.models import Avg, Count, Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.permissions import IsAdmin, IsAdminOrTeacher
from .models import Teacher
from .serializers import TeacherSerializer


def teacher_class_visibility_sets(teacher):
    """
    Return (all_class_pks, all_string_class_ids) used for teacher-scoped student visibility.
    """
    from attendance.models import AttendanceSession
    from exams.models import Exam

    session_class_pks = set(
        AttendanceSession.objects
        .filter(instructor=teacher, school_class__isnull=False)
        .order_by()
        .values_list('school_class_id', flat=True)
        .distinct()
    )
    exam_class_ids = set(
        Exam.objects
        .filter(teacher=teacher)
        .exclude(class_id='')
        .order_by()
        .values_list('class_id', flat=True)
        .distinct()
    )
    assigned_pks = set(teacher.assigned_classes.values_list('id', flat=True))
    junction_ids = set(
        teacher.subject_class_relations.order_by().values_list('class_id', flat=True).distinct()
    )
    all_class_pks = session_class_pks | assigned_pks
    all_string_class_ids = exam_class_ids | junction_ids
    return all_class_pks, all_string_class_ids


def teacher_visible_students_queryset(teacher):
    """Students visible to this teacher (same rules as dashboard)."""
    from django.db.models import Q as DQ
    from students.models import Student

    all_class_pks, all_string_class_ids = teacher_class_visibility_sets(teacher)
    if not all_class_pks and not all_string_class_ids:
        return Student.objects.none()
    student_filter = DQ()
    if all_class_pks:
        student_filter |= DQ(school_class_id__in=list(all_class_pks))
    if all_string_class_ids:
        student_filter |= DQ(class_id__in=list(all_string_class_ids))
    return Student.objects.filter(student_filter).order_by().distinct()


# Ordered weekday labels starting Monday
_WEEK_LABELS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

# All assessment types we surface in the mix chart
_ASSESSMENT_TYPES = [
    ('quiz',       'Quiz'),
    ('midterm',    'Midterm'),
    ('homework',   'Homework'),
    ('lab',        'Lab'),
    ('final',      'Final'),
    ('assignment', 'Assignment'),
    ('oral_exam',  'Oral Exam'),
]


class TeacherViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Teacher management.
    - List/Retrieve: ADMIN, TEACHER (all can view)
    - Create/Update/Delete: ADMIN only
    """
    queryset = Teacher.objects.select_related('user').prefetch_related('assigned_subjects')
    serializer_class = TeacherSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """Override permissions based on action"""
        if self.action in ['create', 'destroy', 'update', 'partial_update']:
            return [IsAdmin()]
        elif self.action in ['list', 'retrieve']:
            return [IsAdminOrTeacher()]
        return super().get_permissions()

    # ──────────────────────────────────────────────────────────────────
    # Dashboard aggregate endpoint
    # ──────────────────────────────────────────────────────────────────

    @action(
        detail=False,
        methods=['get'],
        url_path='dashboard',
        url_name='dashboard',
        permission_classes=[IsAuthenticated],
    )
    def dashboard(self, request):
        """
        GET /api/teachers/dashboard/

        Returns all metrics needed by the Teacher Dashboard in a single request:
          - my_classes          : int
          - students_taught     : int
          - sessions_this_week  : int
          - avg_score           : float | null
          - weekly_activity     : [{name, value}] (Mon–Sun of current ISO week)
          - assessment_mix      : [{name, value}] (counts per exam_type)
          - recent_exams        : list of last 5 exam objects for this teacher
        """
        import traceback
        from django.conf import settings as django_settings

        user = request.user

        # Resolve the Teacher profile
        teacher = getattr(user, 'teacher_profile', None)
        if teacher is None:
            return Response({
                'my_classes': 0,
                'students_taught': 0,
                'sessions_this_week': 0,
                'avg_score': None,
                'weekly_activity': self._empty_week(),
                'assessment_mix': self._empty_mix(),
                'recent_exams': [],
            })

        try:
            # Lazy imports to avoid circular deps at module level
            from attendance.models import AttendanceSession
            from exams.models import Exam, Grade

            # ── 1. My Classes ──────────────────────────────────────────────
            # Use the assigned_classes M2M as the authoritative source for
            # current class assignments.  Historical sessions/exams may still
            # reference classes that have been removed from the teacher, but
            # the "My Classes" card should only show currently assigned ones.

            assigned_qs = teacher.assigned_classes.all().order_by('name')
            my_classes = assigned_qs.count()
            my_classes_list = [
                {'id': c.id, 'name': c.display_name or c.name}
                for c in assigned_qs
            ]

            # ── 2. Students Taught ─────────────────────────────────────────
            students_taught = teacher_visible_students_queryset(teacher).count()


            # ── 3. Sessions This Week ──────────────────────────────────────
            today = date.today()
            week_start = today - timedelta(days=today.weekday())
            week_end   = week_start + timedelta(days=6)

            sessions_this_week = (
                AttendanceSession.objects
                .filter(instructor=teacher, date__gte=week_start, date__lte=week_end)
                .count()
            )

            # ── 4. Average Assessment Score ────────────────────────────────
            # .order_by() clears the default Meta ordering so MS SQL Server
            # does not complain about ORDER BY on non-aggregated columns.
            grades_qs = (
                Grade.objects
                .filter(exam__teacher=teacher)
                .select_related('exam')
                .order_by()          # clear default ordering
            )

            total_pct = 0.0
            grade_count = 0
            for g in grades_qs:
                q_count = g.exam.get_questions_count()
                if q_count and q_count > 0:
                    total_pct += float(g.score) / float(q_count) * 100.0
                    grade_count += 1

            avg_score = round(total_pct / grade_count, 1) if grade_count > 0 else None

            # ── 5. Weekly Activity Chart ───────────────────────────────────
            sessions_week = list(
                AttendanceSession.objects
                .filter(instructor=teacher, date__gte=week_start, date__lte=week_end)
                .values_list('date', flat=True)
            )
            day_counts = {i: 0 for i in range(7)}
            for s_date in sessions_week:
                day_counts[s_date.weekday()] += 1

            weekly_activity = [
                {'name': _WEEK_LABELS[i], 'value': day_counts[i]}
                for i in range(7)
            ]

            # ── 6. Assessment Mix Chart ────────────────────────────────────
            # .order_by() is REQUIRED for MS SQL Server: when using
            # values().annotate(), the default Meta ordering (created_at)
            # is injected into ORDER BY but not GROUP BY, causing SQL error 8127.
            exam_type_qs = (
                Exam.objects
                .filter(teacher=teacher)
                .order_by()          # clear default ordering before grouping
                .values('exam_type')
                .annotate(cnt=Count('id'))
            )
            type_map = {row['exam_type']: row['cnt'] for row in exam_type_qs}

            assessment_mix = [
                {'name': label, 'value': type_map.get(key, 0)}
                for key, label in _ASSESSMENT_TYPES
                if type_map.get(key, 0) > 0
            ]
            if not assessment_mix:
                assessment_mix = [
                    {'name': label, 'value': 0}
                    for key, label in _ASSESSMENT_TYPES
                ]

            # ── 7. Recent Exams (for activity feed) ───────────────────────
            recent_exams_qs = (
                Exam.objects
                .filter(teacher=teacher)
                .select_related('subject')
                .order_by('-created_at')[:5]  # explicit ordering is fine here (no aggregation)
            )
            recent_exams = [
                {
                    'id': e.id,
                    'name': e.name,
                    'exam_type': e.exam_type,
                    'exam_type_display': e.get_exam_type_display(),
                    'subject_name': e.subject.name,
                    'class_id': e.class_id,
                    'grades_count': e.grades.count(),
                    'created_at': e.created_at.isoformat(),
                }
                for e in recent_exams_qs
            ]

            return Response({
                'my_classes': my_classes,
                'my_classes_list': my_classes_list,
                'students_taught': students_taught,
                'sessions_this_week': sessions_this_week,
                'avg_score': avg_score,
                'weekly_activity': weekly_activity,
                'assessment_mix': assessment_mix,
                'recent_exams': recent_exams,
            })

        except Exception as exc:
            tb = traceback.format_exc()
            error_detail = str(exc)
            if django_settings.DEBUG:
                error_detail = tb
            return Response(
                {'detail': f'Dashboard error: {error_detail}'},
                status=500,
            )

    @action(
        detail=False,
        methods=['get'],
        url_path='my-students',
        url_name='my-students',
        permission_classes=[IsAuthenticated],
    )
    def my_students(self, request):
        """
        GET /api/teachers/my-students/

        Per-student stats for the teacher weekly reports UI (same row shape as admin all-stats).
        """
        from students.reporting import build_student_stats_list

        teacher = getattr(request.user, 'teacher_profile', None)
        if teacher is None:
            return Response([])
        qs = teacher_visible_students_queryset(teacher)
        return Response(build_student_stats_list(qs, request))

    # ── helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _empty_week():
        return [{'name': label, 'value': 0} for label in _WEEK_LABELS]

    @staticmethod
    def _empty_mix():
        return [{'name': label, 'value': 0} for _, label in _ASSESSMENT_TYPES]
