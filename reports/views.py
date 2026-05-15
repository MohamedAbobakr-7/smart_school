import os

from django.db.models import Q
from django.http import FileResponse, Http404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.permissions import IsAdminOrTeacher

from .models import Report, WeeklyReport
from .serializers import (
    ReportSerializer,
    WeeklyReportGenerateSerializer,
    WeeklyReportSerializer,
)
from .weekly_report_service import (
    generate_school_and_teacher_reports,
    previous_completed_iso_week,
    upsert_weekly_report,
)


class ReportViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Report management.
    - List/Retrieve: ADMIN, TEACHER (all), PARENT (own children), STUDENT (own)
    - Create/Update/Delete: ADMIN, TEACHER only
    """
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
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
            # ADMIN and TEACHER can see all reports
            return Report.objects.all()
        elif user.is_student():
            # STUDENT can only see their own reports
            if hasattr(user, 'student_profile'):
                return Report.objects.filter(student=user.student_profile)
            return Report.objects.none()
        elif user.is_parent():
            # PARENT can see their children's reports
            if hasattr(user, 'parent_profile'):
                children = user.parent_profile.children.all()
                return Report.objects.filter(student__in=children)
            return Report.objects.none()

        return Report.objects.none()


class WeeklyReportViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Weekly analytics snapshots: dashboards, chart payloads, and PDF export.
    Admins see all scopes; teachers see school-wide plus their own TEACHER rows.
    """
    serializer_class = WeeklyReportSerializer
    permission_classes = [IsAuthenticated]
    queryset = WeeklyReport.objects.all()

    def get_permissions(self):
        if self.action in ['generate', 'download_pdf']:
            return [IsAdminOrTeacher()]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        qs = WeeklyReport.objects.filter(
            status__in=[WeeklyReport.Status.READY, WeeklyReport.Status.FAILED]
        )
        if user.is_admin():
            return qs
        if user.is_teacher() and hasattr(user, 'teacher_profile'):
            tp = user.teacher_profile
            return qs.filter(
                Q(scope=WeeklyReport.Scope.SCHOOL)
                | Q(scope=WeeklyReport.Scope.TEACHER, teacher=tp)
            )
        return WeeklyReport.objects.none()

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx

    @action(detail=False, methods=['get'], url_path='dashboard')
    def dashboard(self, request):
        """
        Analytics dashboard: KPI trend series and latest snapshot for charts.
        Query: ?weeks=8 — number of recent week buckets to include.
        """
        user = request.user
        if not (user.is_admin() or user.is_teacher()):
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        try:
            weeks = int(request.query_params.get('weeks', '8'))
        except ValueError:
            weeks = 8
        weeks = max(1, min(weeks, 52))

        if user.is_admin():
            trend_qs = (
                WeeklyReport.objects.filter(
                    status=WeeklyReport.Status.READY,
                    scope=WeeklyReport.Scope.SCHOOL,
                )
                .order_by('-week_start')[:weeks]
            )
            latest_teacher = None
        else:
            tp = getattr(user, 'teacher_profile', None)
            if not tp:
                return Response({'detail': 'No teacher profile'}, status=status.HTTP_403_FORBIDDEN)
            trend_qs = (
                WeeklyReport.objects.filter(
                    status=WeeklyReport.Status.READY,
                    scope=WeeklyReport.Scope.TEACHER,
                    teacher=tp,
                )
                .order_by('-week_start')[:weeks]
            )
            latest_teacher = WeeklyReport.objects.filter(
                status=WeeklyReport.Status.READY,
                scope=WeeklyReport.Scope.SCHOOL,
            ).order_by('-week_start').first()

        trend = []
        for r in reversed(list(trend_qs)):
            att = r.attendance_stats or {}
            acad = r.academic_stats or {}
            trend.append(
                {
                    'week_start': r.week_start.isoformat(),
                    'week_end': r.week_end.isoformat(),
                    'scope': r.scope,
                    'attendance_rate_percent': att.get('attendance_rate_percent'),
                    'grades_recorded': acad.get('grades_recorded'),
                    'average_score_percent': acad.get('average_score_percent'),
                    'exams_created': acad.get('exams_created'),
                }
            )

        latest = trend_qs.first() if trend_qs else None
        payload = {
            'weeks_requested': weeks,
            'trend': trend,
            'latest': WeeklyReportSerializer(latest, context=self.get_serializer_context()).data
            if latest
            else None,
            'school_context': None,
        }
        if latest_teacher:
            payload['school_context'] = WeeklyReportSerializer(
                latest_teacher, context=self.get_serializer_context()
            ).data

        return Response(payload)

    @action(detail=False, methods=['post'], url_path='generate')
    def generate(self, request):
        """Build or refresh analytics (and optional PDF) for a week."""
        ser = WeeklyReportGenerateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        user = request.user
        if not user.has_any_admin_or_teacher():
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        if data.get('week_start') and data.get('week_end'):
            week_start = data['week_start']
            week_end = data['week_end']
        else:
            week_start, week_end = previous_completed_iso_week()

        write_pdf = data.get('write_pdf', True)
        all_teachers = data.get('all_teachers', False)

        if all_teachers:
            if not user.is_admin():
                return Response(
                    {'detail': 'Only administrators can set all_teachers.'},
                    status=status.HTTP_403_FORBIDDEN,
                )
            reports = generate_school_and_teacher_reports(
                week_start, week_end, write_pdf=write_pdf
            )
            out = WeeklyReportSerializer(
                reports, many=True, context=self.get_serializer_context()
            )
            return Response(out.data, status=status.HTTP_201_CREATED)

        scope = data['scope']
        if scope == WeeklyReport.Scope.SCHOOL:
            if not user.is_admin():
                return Response(
                    {'detail': 'Only administrators can generate school-wide reports.'},
                    status=status.HTTP_403_FORBIDDEN,
                )
            report = upsert_weekly_report(
                week_start, week_end, WeeklyReport.Scope.SCHOOL, None, write_pdf=write_pdf
            )
        else:
            if not hasattr(user, 'teacher_profile'):
                return Response(
                    {'detail': 'Teacher profile required.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            report = upsert_weekly_report(
                week_start,
                week_end,
                WeeklyReport.Scope.TEACHER,
                user.teacher_profile,
                write_pdf=write_pdf,
            )

        return Response(
            WeeklyReportSerializer(report, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['get'], url_path='download-pdf')
    def download_pdf(self, request, pk=None):
        report = self.get_object()
        if not report.pdf_file or not report.pdf_file.name:
            raise Http404('PDF not generated for this report.')
        try:
            f = report.pdf_file.open('rb')
        except FileNotFoundError:
            raise Http404('PDF file missing on disk.')
        filename = os.path.basename(report.pdf_file.name) or 'weekly_report.pdf'
        return FileResponse(f, as_attachment=True, filename=filename)
