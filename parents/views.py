from datetime import date, timedelta

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.permissions import IsAdmin, IsParent
from chatbot.views import ROLE_SUGGESTIONS
from .models import Parent
from .serializers import ParentSerializer


class ParentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Parent management.
    - List/Retrieve: ADMIN, TEACHER (all), PARENT (own data)
    - Create/Update/Delete: ADMIN only
    """
    queryset = Parent.objects.all()
    serializer_class = ParentSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['create', 'destroy', 'update', 'partial_update']:
            return [IsAdmin()]
        elif self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        if user.is_admin() or user.is_teacher():
            return Parent.objects.all()
        elif user.is_parent():
            if hasattr(user, 'parent_profile'):
                return Parent.objects.filter(id=user.parent_profile.id)
            return Parent.objects.none()
        return Parent.objects.none()

    # ── Parent Dashboard ──────────────────────────────────────────────────────

    @action(
        detail=False,
        methods=['get'],
        url_path='dashboard',
        url_name='dashboard',
        permission_classes=[IsAuthenticated],
    )
    def dashboard(self, request):
        """
        GET /api/parents/dashboard/

        Returns KPIs scoped to the logged-in parent's children:
          - children_count
          - avg_attendance_rate  (% | null)
          - avg_score            (% | null)
          - unread_notifications (int)
          - children            [{id, name, attendance_rate, avg_score}]
          - attendance_trend    [{name, value}] combined Mon-Sun this week
          - subject_scores      [{name, value}] avg % per subject across children
          - recent_activity     [{id, title, subtitle, time, tone}]
          - chatbot             {greeting, suggestions} for the chatbot widget
        """
        import traceback
        from django.conf import settings as dj_settings

        user = request.user
        parent = getattr(user, 'parent_profile', None)
        if parent is None:
            return Response({
                'children_count': 0, 'avg_attendance_rate': None,
                'avg_score': None, 'unread_notifications': 0,
                'children': [], 'attendance_trend': [],
                'subject_scores': [], 'recent_activity': [],
                'chatbot': {
                    'greeting': f"Hello {user.get_full_name() or user.username}! How can I help you today?",
                    'suggestions': ROLE_SUGGESTIONS.get('PARENT', []),
                },
            })

        try:
            from attendance.models import Attendance
            from exams.models import Grade
            from notifications.models import Notification

            children = list(parent.children.select_related('user').all())
            children_count = len(children)

            _DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            today      = date.today()
            week_start = today - timedelta(days=today.weekday())
            week_end   = week_start + timedelta(days=6)

            # Per-child stats + aggregate accumulators
            total_att_pct = 0.0
            total_score   = 0.0
            att_count = 0
            score_count = 0
            combined_day_present = {i: 0 for i in range(7)}
            subj_map: dict = {}
            _TONES = ['indigo', 'violet', 'emerald', 'amber']
            recent_raw = []
            children_data = []

            for child in children:
                # Attendance
                child_att = Attendance.objects.filter(student=child).order_by()
                c_total = child_att.count()
                c_present = child_att.filter(status=Attendance.PRESENT).count()
                c_att_pct = round(c_present / c_total * 100, 1) if c_total else None
                if c_att_pct is not None:
                    total_att_pct += c_att_pct
                    att_count += 1

                # This-week trend (combined)
                for row in child_att.filter(
                    date__gte=week_start, date__lte=week_end
                ).values('date', 'status'):
                    if row['status'] == Attendance.PRESENT:
                        combined_day_present[row['date'].weekday()] += 1

                # Grades
                child_grades = (
                    Grade.objects
                    .filter(student=child)
                    .select_related('exam', 'exam__subject')
                    .order_by()
                )
                c_pct_sum = 0.0
                c_grade_cnt = 0
                for g in child_grades:
                    q = g.exam.get_questions_count()
                    if not q:
                        continue
                    pct = float(g.score) / float(q) * 100.0
                    c_pct_sum += pct
                    c_grade_cnt += 1
                    sname = g.exam.subject.name
                    bucket = subj_map.setdefault(sname, [0.0, 0])
                    bucket[0] += pct
                    bucket[1] += 1

                c_avg_score = round(c_pct_sum / c_grade_cnt, 1) if c_grade_cnt else None
                if c_avg_score is not None:
                    total_score += c_avg_score
                    score_count += 1

                child_name = child.user.get_full_name() or child.user.username
                children_data.append({
                    'id': child.id,
                    'name': child_name,
                    'student_id': child.student_id,
                    'attendance_rate': c_att_pct,
                    'avg_score': c_avg_score,
                })

                # Recent grades for this child (activity feed)
                for g in (
                    Grade.objects
                    .filter(student=child)
                    .select_related('exam', 'exam__subject')
                    .order_by('-created_at')[:3]
                ):
                    q = g.exam.get_questions_count() or 1
                    pct = round(float(g.score) / float(q) * 100, 1)
                    recent_raw.append({
                        'ts': g.created_at,
                        'title': f'{child_name}: {g.exam.name}',
                        'subtitle': f'{g.exam.get_exam_type_display()} · {g.exam.subject.name} · {pct}%',
                        'tone': 'indigo',
                    })

            # Averages
            avg_attendance_rate = round(total_att_pct / att_count, 1) if att_count else None
            avg_score = round(total_score / score_count, 1) if score_count else None

            # Unread notifications for this parent's user
            try:
                unread_notifications = Notification.objects.filter(
                    recipient=user, is_read=False
                ).count()
            except Exception:
                unread_notifications = 0

            # Attendance trend
            attendance_trend = [
                {'name': _DAYS[i], 'value': combined_day_present[i]}
                for i in range(7)
            ]

            # Subject scores
            subject_scores = [
                {'name': k, 'value': round(v[0] / v[1], 1)}
                for k, v in subj_map.items() if v[1] > 0
            ]
            subject_scores.sort(key=lambda x: x['value'], reverse=True)

            # Recent activity — sort merged list
            recent_raw.sort(key=lambda x: x['ts'] or date.min, reverse=True)

            def _rel(dt):
                if not dt:
                    return '—'
                diff = date.today().toordinal() - dt.date().toordinal()
                if diff == 0: return 'Today'
                if diff == 1: return 'Yesterday'
                return f'{diff}d ago'

            recent_activity = [
                {
                    'id': str(i),
                    'title': r['title'],
                    'subtitle': r['subtitle'],
                    'time': _rel(r['ts']),
                    'tone': _TONES[i % len(_TONES)],
                }
                for i, r in enumerate(recent_raw[:8])
            ]

            return Response({
                'children_count': children_count,
                'avg_attendance_rate': avg_attendance_rate,
                'avg_score': avg_score,
                'unread_notifications': unread_notifications,
                'children': children_data,
                'attendance_trend': attendance_trend,
                'subject_scores': subject_scores,
                'recent_activity': recent_activity,
                'chatbot': {
                    'greeting': f"Hello {user.get_full_name() or user.username}! How can I help you today?",
                    'suggestions': ROLE_SUGGESTIONS.get('PARENT', []),
                },
            })

        except Exception as exc:
            tb = traceback.format_exc()
            return Response(
                {'detail': f'Dashboard error: {tb if dj_settings.DEBUG else str(exc)}'},
                status=500,
            )
