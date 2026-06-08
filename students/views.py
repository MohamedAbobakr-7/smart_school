import logging

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response

from smartSchool.messages import (
    MSG_ALL_STUDENTS_HAVE_IDS, MSG_STUDENT_ID_GENERATED,
    MSG_INVALID_DATE_FORMAT, MSG_NO_IMAGE_PROVIDED,
    MSG_INVALID_FILE_TYPE, MSG_PHOTO_SAVED_NO_ID,
    MSG_FACE_REGISTERED_SUCCESS, MSG_FACE_REGISTRATION_FAILED,
    MSG_PHOTO_SAVED_SERVICE_UNAVAILABLE, MSG_DASHBOARD_ERROR,
)
from users.permissions import IsAdmin, IsAdminOrTeacher
from .models import Student
from .serializers import StudentSerializer

logger = logging.getLogger(__name__)


class StudentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Student management.
    - List/Retrieve: ADMIN, TEACHER, PARENT (own children), STUDENT (own)
    - Create/Update/Delete: ADMIN, TEACHER only
    - register-face: upload a photo and register the face encoding
    - face-status: check if the student has a registered face
    """
    queryset = Student.objects.select_related('user', 'parent').prefetch_related('subjects')
    serializer_class = StudentSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.action in ['create', 'destroy', 'update', 'partial_update', 'register_face', 'backfill_ids']:
            return [IsAdminOrTeacher()]
        elif self.action in ['list', 'retrieve', 'face_status']:
            return [IsAuthenticated()]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        qs = Student.objects.select_related('user', 'parent').prefetch_related('subjects')

        class_id = self.request.query_params.get('class_id')
        parent_id = self.request.query_params.get('parent_id')
        subject_id = self.request.query_params.get('subject_id')
        if class_id:
            qs = qs.filter(class_id=class_id)
        if parent_id:
            qs = qs.filter(parent_id=parent_id)
        if subject_id:
            qs = qs.filter(subjects__id=subject_id)

        if user.is_admin() or user.is_teacher():
            return qs.distinct()
        elif user.is_student():
            if hasattr(user, 'student_profile'):
                return qs.filter(id=user.student_profile.id).distinct()
            return qs.none()
        elif user.is_parent():
            if hasattr(user, 'parent_profile'):
                return qs.filter(parent=user.parent_profile).distinct()
            return qs.none()
        return qs.none()

    @action(
        detail=False,
        methods=['post'],
        url_path='backfill-ids',
        url_name='backfill-ids',
        permission_classes=[IsAdmin],
    )
    def backfill_ids(self, request):
        """
        POST /api/students/backfill-ids/
        Admin-only: assign auto-generated Student IDs to every student with a blank ID
        (null, empty, or whitespace). Use after bulk-creating students with "assign ID later".
        Returns the count of updated students and a preview list.
        """
        from .utils import generate_student_id, students_missing_ids_queryset

        qs = students_missing_ids_queryset()
        total_missing = qs.count()

        if total_missing == 0:
            return Response({
                'updated': 0,
                'message': str(MSG_ALL_STUDENTS_HAVE_IDS),
                'students': [],
            })

        updated_students = []
        for student in list(qs):
            new_id = generate_student_id(school_class=student.school_class)
            student.student_id = new_id
            student.save(update_fields=['student_id'])
            updated_students.append({
                'id': student.id,
                'student_id': new_id,
                'name': student.user.get_full_name() or student.user.username,
            })

        return Response({
            'updated': len(updated_students),
            'message': str(MSG_STUDENT_ID_GENERATED).format(count=len(updated_students)),
            'students': updated_students,
        })

    @action(
        detail=False,
        methods=['get'],
        url_path='all-stats',
        url_name='all-stats',
        permission_classes=[IsAdmin],
    )
    def all_stats(self, request):
        """
        GET /api/students/all-stats/

        Admin-only: per-student attendance and grade aggregates for reporting dashboards.
        """
        from .reporting import build_student_stats_list

        qs = self.get_queryset()
        return Response(build_student_stats_list(qs, request))

    # ── Student Weekly Report ───────────────────────────────────────────

    @action(
        detail=False,
        methods=['get'],
        url_path='weekly-report',
        url_name='weekly-report',
        permission_classes=[IsAuthenticated],
    )
    def weekly_report(self, request):
        """
        GET /api/students/weekly-report/

        Returns weekly analytics for the logged-in student:
          - week_start, week_end
          - attendance_stats: {total, present, absent, rate_percent, by_day}
          - academic_stats: {grades_count, avg_score_percent, by_subject}
          - insights: [{level, text}]
        Optional query params: ?week_start=YYYY-MM-DD&week_end=YYYY-MM-DD
        Defaults to the last completed ISO week (Mon–Sun).
        """
        from datetime import date, timedelta
        from collections import defaultdict
        from attendance.models import Attendance
        from exams.models import Grade

        user = request.user
        student = getattr(user, 'student_profile', None)
        if student is None:
            return Response({
                'week_start': None, 'week_end': None,
                'attendance_stats': {}, 'academic_stats': {},
                'insights': [],
            })

        # ── Determine week window ────────────────────────────────────
        ws_param = request.query_params.get('week_start')
        we_param = request.query_params.get('week_end')
        if ws_param and we_param:
            try:
                week_start = date.fromisoformat(ws_param)
                week_end = date.fromisoformat(we_param)
            except ValueError:
                return Response(
                    {'detail': str(MSG_INVALID_DATE_FORMAT)},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            # Default: last completed ISO week
            today = date.today()
            this_monday = today - timedelta(days=today.weekday())
            last_sunday = this_monday - timedelta(days=1)
            last_monday = last_sunday - timedelta(days=6)
            week_start = last_monday
            week_end = last_sunday

        # ── Attendance ───────────────────────────────────────────────
        att_qs = Attendance.objects.filter(
            student=student,
            date__gte=week_start,
            date__lte=week_end,
        )
        total_att = att_qs.count()
        present = att_qs.filter(status=Attendance.PRESENT).count()
        absent = att_qs.filter(status=Attendance.ABSENT).count()
        rate_pct = round(present / total_att * 100, 1) if total_att else 0.0

        by_day = defaultdict(lambda: {'present': 0, 'absent': 0})
        for row in att_qs.values('date', 'status'):
            key = row['date'].isoformat() if hasattr(row['date'], 'isoformat') else str(row['date'])
            if row['status'] == Attendance.PRESENT:
                by_day[key]['present'] += 1
            else:
                by_day[key]['absent'] += 1

        day_labels = []
        present_series = []
        absent_series = []
        cur = week_start
        while cur <= week_end:
            key = cur.isoformat()
            day_labels.append(cur.strftime('%a %m/%d'))
            present_series.append(by_day[key]['present'])
            absent_series.append(by_day[key]['absent'])
            cur += timedelta(days=1)

        attendance_stats = {
            'total_records': total_att,
            'present': present,
            'absent': absent,
            'rate_percent': rate_pct,
            'by_day': {
                'labels': day_labels,
                'present': present_series,
                'absent': absent_series,
            },
        }

        # ── Grades / Academic ────────────────────────────────────────
        grade_qs = Grade.objects.filter(
            student=student,
            created_at__date__gte=week_start,
            created_at__date__lte=week_end,
        ).select_related('exam', 'exam__subject')

        grades_count = grade_qs.count()
        total_pct = 0.0
        subj_map: dict = {}
        for g in grade_qs:
            pct = g.get_percentage()
            if not pct:
                continue
            total_pct += float(pct)
            sname = g.exam.subject.name
            bucket = subj_map.setdefault(sname, [0.0, 0])
            bucket[0] += float(pct)
            bucket[1] += 1

        avg_score_pct = round(total_pct / grades_count, 1) if grades_count else None

        subject_labels = sorted(subj_map.keys())
        subject_avgs = [
            round(subj_map[s][0] / subj_map[s][1], 1) for s in subject_labels if subj_map[s][1] > 0
        ]

        academic_stats = {
            'grades_count': grades_count,
            'avg_score_percent': avg_score_pct,
            'by_subject': {
                'labels': subject_labels,
                'averages': subject_avgs,
            },
        }

        # ── Insights ─────────────────────────────────────────────────
        insights = []
        if total_att:
            if rate_pct >= 90:
                insights.append({'level': 'positive', 'text': f'Your attendance rate was strong ({rate_pct}%).'})
            elif rate_pct < 75:
                insights.append({'level': 'warning', 'text': f'Your attendance rate was {rate_pct}%; try to attend more sessions.'})
            else:
                insights.append({'level': 'neutral', 'text': f'Your attendance rate was {rate_pct}%.'})
        else:
            insights.append({'level': 'neutral', 'text': 'No attendance records in this week.'})

        if avg_score_pct is not None:
            if avg_score_pct >= 80:
                insights.append({'level': 'positive', 'text': f'Your average score was {avg_score_pct}% — great work!'})
            elif avg_score_pct < 60:
                insights.append({'level': 'warning', 'text': f'Your average score was {avg_score_pct}%; consider reviewing difficult topics.'})
            else:
                insights.append({'level': 'neutral', 'text': f'Your average score was {avg_score_pct}%.'})
        elif grades_count == 0:
            insights.append({'level': 'neutral', 'text': 'No grades recorded in this week.'})

        insights.append({
            'level': 'neutral',
            'text': f'Reporting window: {week_start.isoformat()} to {week_end.isoformat()}.',
        })

        return Response({
            'week_start': week_start.isoformat(),
            'week_end': week_end.isoformat(),
            'attendance_stats': attendance_stats,
            'academic_stats': academic_stats,
            'insights': insights,
        })

    # ── Student Dashboard ───────────────────────────────────────────

    @action(
        detail=False,
        methods=['get'],
        url_path='dashboard',
        url_name='dashboard',
        permission_classes=[IsAuthenticated],
    )
    def dashboard(self, request):
        """
        GET /api/students/dashboard/

        Returns KPIs for the logged-in student:
          - subjects_count, exams_taken
          - attendance_rate  (% | null)
          - avg_score        (% | null)
          - attendance_trend [{name, value}] last 7 days
          - subject_scores   [{name, value}] avg % per subject
          - recent_grades    [{id, title, subtitle, time, tone}] last 5
        """
        import traceback
        from datetime import date, timedelta
        from django.conf import settings as dj_settings

        user = request.user
        student = getattr(user, 'student_profile', None)
        if student is None:
            return Response({
                'subjects_count': 0, 'exams_taken': 0,
                'attendance_rate': None, 'avg_score': None,
                'attendance_trend': [], 'subject_scores': [],
                'recent_grades': [],
            })

        try:
            from attendance.models import Attendance
            from exams.models import Grade

            # ── Subjects ────────────────────────────────────────────
            subjects_count = student.subjects.count()

            # ── Grades ──────────────────────────────────────────────
            grades_qs = (
                Grade.objects
                .filter(student=student)
                .select_related('exam', 'exam__subject')
                .order_by()
            )
            exams_taken = grades_qs.count()

            total_pct = 0.0
            grade_cnt = 0
            subj_map: dict = {}
            for g in grades_qs:
                pct = g.get_percentage()
                if not pct:
                    continue
                total_pct += float(pct)
                grade_cnt += 1
                sname = g.exam.subject.name
                bucket = subj_map.setdefault(sname, [0.0, 0])
                bucket[0] += float(pct)
                bucket[1] += 1

            avg_score = round(total_pct / grade_cnt, 1) if grade_cnt else None

            subject_scores = [
                {'name': k, 'value': round(v[0] / v[1], 1)}
                for k, v in subj_map.items() if v[1] > 0
            ]
            subject_scores.sort(key=lambda x: x['value'], reverse=True)

            # ── Attendance ─────────────────────────────────────────
            att_qs = Attendance.objects.filter(student=student).order_by()
            total_att = att_qs.count()
            present   = att_qs.filter(status=Attendance.PRESENT).count()
            attendance_rate = round(present / total_att * 100, 1) if total_att else None

            # Last 7 days trend — fall back to previous week if current week is empty
            today = date.today()
            _DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            week_start = today - timedelta(days=today.weekday())
            week_end   = week_start + timedelta(days=6)

            week_att = att_qs.filter(date__gte=week_start, date__lte=week_end)
            if week_att.count() == 0:
                prev_end   = week_start - timedelta(days=1)
                prev_start = prev_end - timedelta(days=6)
                week_start = prev_start
                week_end   = prev_end
                week_att   = att_qs.filter(date__gte=week_start, date__lte=week_end)

            day_present = {i: 0 for i in range(7)}
            for row in week_att.values('date', 'status'):
                if row['status'] == Attendance.PRESENT:
                    day_present[row['date'].weekday()] += 1

            attendance_trend = [
                {'name': _DAYS[i], 'value': day_present[i]}
                for i in range(7)
            ]

            # ── Recent grades as activity ─────────────────────────
            recent_qs = (
                Grade.objects
                .filter(student=student)
                .select_related('exam', 'exam__subject')
                .order_by('-created_at')[:5]
            )
            _TONES = ['indigo', 'violet', 'emerald', 'amber']

            def _rel(dt):
                if not dt:
                    return '—'
                diff = date.today().toordinal() - dt.date().toordinal()
                if diff == 0: return 'Today'
                if diff == 1: return 'Yesterday'
                return f'{diff}d ago'

            recent_grades = []
            for i, g in enumerate(recent_qs):
                pct = round(float(g.get_percentage()), 1)
                recent_grades.append({
                    'id': str(g.id),
                    'title': g.exam.name,
                    'subtitle': f'{g.exam.get_exam_type_display()} · {g.exam.subject.name} · {pct}%',
                    'time': _rel(g.created_at),
                    'tone': _TONES[i % len(_TONES)],
                })

            return Response({
                'subjects_count': subjects_count,
                'exams_taken': exams_taken,
                'attendance_rate': attendance_rate,
                'avg_score': avg_score,
                'attendance_trend': attendance_trend,
                'subject_scores': subject_scores,
                'recent_grades': recent_grades,
            })

        except Exception as exc:
            tb = traceback.format_exc()
            return Response(
                {'detail': str(MSG_DASHBOARD_ERROR).format(error=tb if dj_settings.DEBUG else str(exc))},
                status=500,
            )


    @action(detail=True, methods=['post'], url_path='register-face',
            parser_classes=[MultiPartParser, FormParser])
    def register_face(self, request, pk=None):
        """
        POST /api/students/{id}/register-face/
        Upload a face photo for a student.
        Steps:
          1. Validate image is provided
          2. Save image to student.photo
          3. Call face recognition service to register/encode face (skipped until student_id is set)
          4. Set face_registered = True on success
          5. Return result with status info
        """
        student = self.get_object()
        image_file = request.FILES.get('photo')

        if not image_file:
            return Response(
                {'error': str(MSG_NO_IMAGE_PROVIDED)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate file type
        content_type = image_file.content_type or ''
        if not content_type.startswith('image/'):
            return Response(
                {'error': str(MSG_INVALID_FILE_TYPE).format(content_type=content_type)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Save photo to student record
        student.photo = image_file
        student.face_registered = False          # reset until face service confirms
        student.save(update_fields=['photo', 'face_registered'])

        student.refresh_from_db()
        sid = (student.student_id or '').strip()
        if not sid:
            # Face microservice keys by school student_id; skip until one is assigned.
            return Response(
                {
                    'success': True,
                    'message': str(MSG_PHOTO_SAVED_NO_ID),
                    'photo_saved': True,
                    'face_registered': False,
                    'student_id': None,
                    'photo_url': request.build_absolute_uri(student.photo.url),
                },
                status=status.HTTP_200_OK,
            )

        # Call face recognition service
        try:
            from attendance.face_recognition_client import get_face_recognition_client
            client = get_face_recognition_client()

            with student.photo.open('rb') as f:
                result = client.register_face(sid, f)

            if result.get('success'):
                student.face_registered = True
                student.save(update_fields=['face_registered'])
                return Response({
                    'success': True,
                    'message': result.get('message', str(MSG_FACE_REGISTERED_SUCCESS)),
                    'student_id': student.student_id,
                    'photo_url': request.build_absolute_uri(student.photo.url),
                    'face_registered': True,
                }, status=status.HTTP_200_OK)
            else:
                # Photo saved but face encoding failed
                error_msg = result.get('error', 'unknown')
                logger.warning(f'Face registration failed for student {sid}: {error_msg}')
                return Response({
                    'success': False,
                    'message': result.get('message', str(MSG_FACE_REGISTRATION_FAILED)),
                    'error': error_msg,
                    'photo_saved': True,
                    'face_registered': False,
                    'photo_url': request.build_absolute_uri(student.photo.url),
                }, status=status.HTTP_200_OK)   # 200 because photo WAS saved

        except Exception as exc:
            logger.error(f'register_face error for student {sid}: {exc}')
            # Photo is saved; face service is offline / raised
            return Response({
                'success': False,
                'message': str(MSG_PHOTO_SAVED_SERVICE_UNAVAILABLE),
                'error': str(exc),
                'photo_saved': True,
                'face_registered': False,
                'photo_url': request.build_absolute_uri(student.photo.url),
            }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='face-status')
    def face_status(self, request, pk=None):
        """
        GET /api/students/{id}/face-status/
        Returns face registration status from DB and optionally from the face service.
        """
        student = self.get_object()
        try:
            from attendance.face_recognition_client import get_face_recognition_client
            client = get_face_recognition_client()
            service_status = client.get_face_status(student.student_id)
        except Exception as exc:
            service_status = {'success': False, 'error': str(exc)}

        return Response({
            'student_id': student.student_id,
            'face_registered_db': student.face_registered,
            'photo_url': (
                request.build_absolute_uri(student.photo.url)
                if student.photo else None
            ),
            'service': service_status,
        })
