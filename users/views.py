from datetime import date, timedelta

from django.db.models import Count, Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from smartSchool.messages import MSG_INVALID_ROLE, MSG_DASHBOARD_ERROR
from .models import User
from .serializers import UserCreateSerializer, UserSerializer, ProfileSerializer
from .permissions import IsAdmin, IsAdminOrOwner


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for User management.
    - List/Retrieve: Authenticated users can view
    - Create/Update/Delete: Only ADMIN can perform
    - Users can update their own profile
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Use different serializer for create action"""
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    def get_permissions(self):
        """Override permissions based on action"""
        if self.action in ['create', 'destroy', 'update', 'partial_update']:
            return [IsAdmin()]
        elif self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return super().get_permissions()

    def get_queryset(self):
        """Filter queryset based on user role"""
        user = self.request.user

        if user.is_admin():
            return User.objects.all()
        elif user.is_teacher():
            return User.objects.all()
        elif user.is_student():
            return User.objects.filter(id=user.id)
        elif user.is_parent():
            if hasattr(user, 'parent_profile'):
                children_ids = user.parent_profile.children.values_list('user_id', flat=True)
                return User.objects.filter(id__in=[user.id] + list(children_ids))
            return User.objects.filter(id=user.id)

        return User.objects.none()

    @action(detail=False, methods=['get', 'patch'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Get or update current user's profile.

        GET  /api/users/me/  — returns full profile including role-specific data.
        PATCH /api/users/me/ — updates editable fields (first_name, last_name,
                                email, phone_number, address).
        """
        if request.method == 'PATCH':
            serializer = ProfileSerializer(
                request.user, data=request.data, partial=True,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

        serializer = ProfileSerializer(request.user, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAdmin])
    def by_role(self, request):
        """Get users filtered by role (ADMIN only)"""
        role = request.query_params.get('role')
        if role and role in [User.Role.ADMIN, User.Role.TEACHER, User.Role.STUDENT, User.Role.PARENT]:
            users = User.objects.filter(role=role)
            serializer = self.get_serializer(users, many=True)
            return Response(serializer.data)
        return Response({'error': str(MSG_INVALID_ROLE)}, status=400)

    # ──────────────────────────────────────────────────────────────────────────
    # Admin dashboard aggregate  GET /api/users/admin-dashboard/
    # ──────────────────────────────────────────────────────────────────────────

    @action(
        detail=False,
        methods=['get'],
        url_path='admin-dashboard',
        url_name='admin_dashboard',
        permission_classes=[IsAdmin],
    )
    def admin_dashboard(self, request):
        """
        Returns all school-wide KPIs needed by AdminDashboard in one request:
          - total_students, total_teachers, total_classes, total_subjects
          - attendance_rate_this_week   (%)
          - avg_score                   (% | null)
          - weekly_attendance           [{name, present, absent}] Mon-Sun
          - subject_scores              [{name, value}] avg % per subject
          - recent_activity             [{id, title, subtitle, time, tone}]
        """
        import traceback
        from django.conf import settings as dj_settings

        try:
            from attendance.models import Attendance, AttendanceSession
            from classes.models import SchoolClass
            from exams.models import Exam, Grade
            from students.models import Student
            from subjects.models import Subject
            from teachers.models import Teacher

            # ── Counts ────────────────────────────────────────────────────────
            total_students  = Student.objects.count()
            total_teachers  = Teacher.objects.count()
            total_classes   = SchoolClass.objects.count()
            total_subjects  = Subject.objects.count()

            # ── This week window ──────────────────────────────────────────────
            today      = date.today()
            week_start = today - timedelta(days=today.weekday())
            week_end   = week_start + timedelta(days=6)

            att_week = Attendance.objects.filter(
                date__gte=week_start, date__lte=week_end
            )
            total_att = att_week.count()
            present   = att_week.filter(status=Attendance.PRESENT).count()
            attendance_rate = round(present / total_att * 100, 1) if total_att else None

            # ── Avg Score (all-time) ───────────────────────────────────────────
            all_grades = (
                Grade.objects
                .select_related('exam')
                .order_by()
            )
            total_pct  = 0.0
            grade_cnt  = 0
            for g in all_grades:
                q = g.exam.get_questions_count()
                if q and q > 0:
                    total_pct += float(g.score) / float(q) * 100.0
                    grade_cnt += 1
            avg_score = round(total_pct / grade_cnt, 1) if grade_cnt else None

            # ── Weekly Attendance Trend (Mon-Sun) ─────────────────────────────
            _DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            day_present = {i: 0 for i in range(7)}
            day_absent  = {i: 0 for i in range(7)}
            for row in att_week.values('date', 'status'):
                wd = row['date'].weekday()
                if row['status'] == Attendance.PRESENT:
                    day_present[wd] += 1
                else:
                    day_absent[wd]  += 1

            weekly_attendance = [
                {'name': _DAYS[i], 'present': day_present[i], 'absent': day_absent[i]}
                for i in range(7)
            ]

            # ── Subject Score Breakdown ────────────────────────────────────────
            subj_scores_map: dict = {}
            for g in (
                Grade.objects
                .select_related('exam', 'exam__subject')
                .order_by()
            ):
                q = g.exam.get_questions_count()
                if not q:
                    continue
                name = g.exam.subject.name
                bucket = subj_scores_map.setdefault(name, [0.0, 0])
                bucket[0] += float(g.score) / float(q) * 100.0
                bucket[1] += 1

            subject_scores = [
                {'name': k, 'value': round(v[0] / v[1], 1)}
                for k, v in subj_scores_map.items()
                if v[1] > 0
            ]
            subject_scores.sort(key=lambda x: x['value'], reverse=True)

            # ── Recent Activity (last 5 exams + last 5 sessions combined) ─────
            recent_exams = list(
                Exam.objects
                .select_related('teacher__user', 'subject')
                .order_by('-created_at')[:5]
            )
            recent_sessions = list(
                AttendanceSession.objects
                .select_related('instructor__user')
                .order_by('-started_at')[:5]
            )

            _TONES = ['indigo', 'violet', 'emerald', 'amber']

            def _rel(dt):
                if not dt:
                    return '—'
                diff = date.today().toordinal() - (
                    dt.date().toordinal() if hasattr(dt, 'date') else dt.toordinal()
                )
                if diff == 0: return 'Today'
                if diff == 1: return 'Yesterday'
                return f'{diff}d ago'

            activity_raw = []
            for e in recent_exams:
                tname = e.teacher.user.get_full_name() or e.teacher.user.username
                activity_raw.append({
                    'ts': e.created_at,
                    'title': e.name,
                    'subtitle': f'{e.get_exam_type_display()} · {e.subject.name} · {tname}',
                    'tone': 'indigo',
                })
            for s in recent_sessions:
                tname = (s.instructor.user.get_full_name() or s.instructor.user.username) if s.instructor else '—'
                activity_raw.append({
                    'ts': s.started_at or s.updated_at,
                    'title': f'Session: {s.class_name or "Attendance"}',
                    'subtitle': f'Instructor: {tname} · {s.get_status_display()}',
                    'tone': 'emerald',
                })

            activity_raw.sort(key=lambda x: x['ts'] or date.min, reverse=True)
            recent_activity = [
                {
                    'id': str(i),
                    'title': r['title'],
                    'subtitle': r['subtitle'],
                    'time': _rel(r['ts']),
                    'tone': r['tone'],
                }
                for i, r in enumerate(activity_raw[:8])
            ]

            return Response({
                'total_students': total_students,
                'total_teachers': total_teachers,
                'total_classes': total_classes,
                'total_subjects': total_subjects,
                'attendance_rate': attendance_rate,
                'avg_score': avg_score,
                'weekly_attendance': weekly_attendance,
                'subject_scores': subject_scores,
                'recent_activity': recent_activity,
            })

        except Exception as exc:
            tb = traceback.format_exc()
            return Response(
                {'detail': str(MSG_DASHBOARD_ERROR).format(error=tb if dj_settings.DEBUG else str(exc))},
                status=500,
            )
