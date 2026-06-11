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
    # Grade is now a CharField (e.g. '5', 'KG'), so find matching SchoolClass PKs
    exam_grade_levels = set(
        Exam.objects
        .filter(teacher=teacher)
        .order_by()
        .values_list('grade', flat=True)
        .distinct()
    )
    from classes.models import SchoolClass
    exam_grade_pks = set()
    for gl in exam_grade_levels:
        if gl == 'KG':
            matching = SchoolClass.objects.filter(name__icontains='kg')
        else:
            matching = SchoolClass.objects.filter(name__icontains=f'Grade {gl}') | SchoolClass.objects.filter(name__icontains=gl)
        exam_grade_pks.update(matching.values_list('id', flat=True))
    assigned_pks = set(teacher.assigned_classes.values_list('id', flat=True))
    junction_ids = set(
        teacher.subject_class_relations.order_by().values_list('class_id', flat=True).distinct()
    )
    all_class_pks = session_class_pks | assigned_pks | exam_grade_pks
    all_string_class_ids = junction_ids
    return all_class_pks, all_string_class_ids


def _build_class_id_lookup():
    """
    Build a dict mapping multiple string key formats to SchoolClass PKs.

    For each SchoolClass we register:
      - display_name  (e.g. "Grade 10 - A")
      - name          (e.g. "Grade 10")
      - abbreviated   (e.g. "G10-A", "10-A")  — parsed from name + section

    This lets us resolve TeacherSubjectClass.class_id strings (which may
    use any of these formats) to the correct SchoolClass PKs.
    """
    import re
    from classes.models import SchoolClass

    lookup: dict[str, int] = {}
    for sc in SchoolClass.objects.all():
        lookup[sc.display_name] = sc.id
        lookup[sc.name] = sc.id
        if sc.section:
            # Extract grade numbers from name (e.g. "Grade 10" → "10")
            for num in re.findall(r'\d+', sc.name):
                lookup[f'G{num}-{sc.section}'] = sc.id
                lookup[f'{num}-{sc.section}'] = sc.id
                lookup[f'Grade{num}-{sc.section}'] = sc.id
                lookup[f'Grade {num}-{sc.section}'] = sc.id
    return lookup


def teacher_assigned_students_queryset(teacher):
    """Students enrolled in classes currently assigned to this teacher."""
    from students.models import Student

    assigned_pks = list(teacher.assigned_classes.values_list('id', flat=True))
    if not assigned_pks:
        return Student.objects.none()
    return Student.objects.filter(school_class_id__in=assigned_pks).order_by().distinct()


def teacher_visible_students_queryset(teacher):
    """Students visible to this teacher (includes historical sessions/exams)."""
    from django.db.models import Q as DQ
    from students.models import Student

    all_class_pks, all_string_class_ids = teacher_class_visibility_sets(teacher)

    # Resolve string class_ids (from TeacherSubjectClass) to SchoolClass PKs
    # so students linked via the school_class FK are also found, even if
    # their class_id CharField is empty or uses a different format.
    if all_string_class_ids:
        lookup = _build_class_id_lookup()
        resolved_pks = set()
        for cid in all_string_class_ids:
            pk = lookup.get(cid)
            if pk:
                resolved_pks.add(pk)
        all_class_pks |= resolved_pks

    if not all_class_pks and not all_string_class_ids:
        return Student.objects.none()

    # Build OR filter carefully — an empty Q() matches EVERYTHING, so
    # never start with Q(). Collect conditions into a list and combine.
    parts = []
    if all_class_pks:
        parts.append(DQ(school_class_id__in=list(all_class_pks)))
    if all_string_class_ids:
        parts.append(DQ(class_id__in=list(all_string_class_ids)))
    if not parts:
        return Student.objects.none()

    student_filter = parts[0]
    for p in parts[1:]:
        student_filter |= p

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
            from students.models import Student

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
            assigned_class_ids = list(teacher.assigned_classes.values_list('id', flat=True))
            students_taught = Student.objects.filter(
                school_class_id__in=assigned_class_ids
            ).count() if assigned_class_ids else 0


            # ── 3. Sessions This Week ──────────────────────────────────────
            today = date.today()
            week_start = today - timedelta(days=today.weekday())
            week_end   = week_start + timedelta(days=6)

            # If the current week has zero sessions for this teacher,
            # fall back to the previous completed week so the chart is useful.
            if not AttendanceSession.objects.filter(
                instructor=teacher, date__gte=week_start, date__lte=week_end
            ).exists():
                prev_end   = week_start - timedelta(days=1)
                prev_start = prev_end - timedelta(days=6)
                week_start = prev_start
                week_end   = prev_end

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
                pct = g.get_percentage()
                if pct is not None:
                    total_pct += float(pct)
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

            # ── 5b. Weekly attendance trend (assigned classes only) ────────
            from attendance.models import Attendance
            att_week = Attendance.objects.filter(
                date__gte=week_start,
                date__lte=week_end,
                student__school_class_id__in=assigned_class_ids,
            ) if assigned_class_ids else Attendance.objects.none()

            day_present = {i: 0 for i in range(7)}
            day_absent = {i: 0 for i in range(7)}
            for row in att_week.values('date', 'status'):
                wd = row['date'].weekday()
                if row['status'] == Attendance.PRESENT:
                    day_present[wd] += 1
                else:
                    day_absent[wd] += 1

            weekly_attendance = [
                {'name': _WEEK_LABELS[i], 'present': day_present[i], 'absent': day_absent[i]}
                for i in range(7)
            ]

            total_att_week = att_week.count()
            present_week = att_week.filter(status=Attendance.PRESENT).count()
            attendance_rate = (
                round(present_week / total_att_week * 100, 1) if total_att_week else None
            )

            # ── 5c. Per-class stats (assigned classes only) ────────────────
            from students.reporting import build_student_stats_list

            class_stats = []
            if assigned_class_ids:
                for cls in assigned_qs:
                    cls_students = Student.objects.filter(school_class_id=cls.id)
                    cls_rows = build_student_stats_list(cls_students, request, teacher=teacher)
                    att_pcts = [r['attendance_pct'] for r in cls_rows if r['attendance_pct'] is not None]
                    grd_avgs = [r['avg_grade'] for r in cls_rows if r['avg_grade'] is not None]
                    class_stats.append({
                        'id': cls.id,
                        'name': cls.display_name or cls.name,
                        'student_count': len(cls_rows),
                        'attendance_rate': round(sum(att_pcts) / len(att_pcts), 1) if att_pcts else None,
                        'avg_grade': round(sum(grd_avgs) / len(grd_avgs), 1) if grd_avgs else None,
                    })

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
                    'grade': e.grade,
                    'grade_name': e.get_grade_display(),
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
                'attendance_rate': attendance_rate,
                'weekly_attendance': weekly_attendance,
                'class_stats': class_stats,
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
        Only includes grades from the teacher's assigned subjects so the
 report reflects their own subject performance.
        """
        from students.reporting import build_student_stats_list

        teacher = getattr(request.user, 'teacher_profile', None)
        if teacher is None:
            return Response([])
        qs = teacher_assigned_students_queryset(teacher)
        return Response(build_student_stats_list(qs, request, teacher=teacher))

    # ── helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _empty_week():
        return [{'name': label, 'value': 0} for label in _WEEK_LABELS]

    @staticmethod
    def _empty_mix():
        return [{'name': label, 'value': 0} for _, label in _ASSESSMENT_TYPES]
