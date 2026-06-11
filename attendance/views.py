from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils import timezone
from datetime import date
from smartSchool.messages import (
    MSG_INSTRUCTOR_ONLY, MSG_SESSION_ID_REQUIRED, MSG_IMAGE_FILE_REQUIRED,
    MSG_ACTIVE_SESSION_NOT_FOUND, MSG_ONLY_OWN_SESSIONS,
    MSG_FACE_DETECTION_FAILED, MSG_PROCESSING_RESULT,
    MSG_DUPLICATE_ACTIVE_SESSION, MSG_SESSION_NOT_ACTIVE,
    MSG_SESSION_COMPLETED, MSG_SESSION_CANCELLED,
    MSG_STUDENT_CLASS_MISMATCH,
)
from users.permissions import IsAdmin, IsAdminOrTeacher, IsTeacher, IsStudent, IsParent
from .models import Attendance, AttendanceSession
from .serializers import AttendanceSerializer, AttendanceSessionSerializer
from .face_recognition_client import get_face_recognition_client
from students.models import Student
from teachers.models import Teacher
from notifications import services as notification_services
from notifications.models import Notification


class AttendanceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Attendance management.
    - List/Retrieve: ADMIN, TEACHER (all), PARENT (own children), STUDENT (own)
    - Create/Update/Delete: TEACHER only (admin can only view attendance records)
    """
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """Override permissions based on action"""
        if self.action in ['create', 'destroy', 'update', 'partial_update', 'process_classroom_image']:
            return [IsTeacher()]
        elif self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return super().get_permissions()

    def get_queryset(self):
        """Filter queryset based on user role"""
        user = self.request.user
        
        if user.is_admin() or user.is_teacher():
            return Attendance.objects.all()
        elif user.is_student():
            if hasattr(user, 'student_profile'):
                return Attendance.objects.filter(student=user.student_profile)
            return Attendance.objects.none()
        elif user.is_parent():
            if hasattr(user, 'parent_profile'):
                children = user.parent_profile.children.all()
                return Attendance.objects.filter(student__in=children)
            return Attendance.objects.none()
        
        return Attendance.objects.none()

    def create(self, request, *args, **kwargs):
        """Override create to perform an UPSERT based on student and date.
        If a record already exists, update it instead of returning a 400 duplicate error."""
        student_id = request.data.get('student')
        att_date = request.data.get('date')
        
        if student_id and att_date:
            existing = Attendance.objects.filter(student_id=student_id, date=att_date).first()
            if existing:
                serializer = self.get_serializer(existing, data=request.data, partial=True)
                serializer.is_valid(raise_exception=True)
                self.perform_update(serializer)
                return Response(serializer.data, status=status.HTTP_200_OK)
                
        return super().create(request, *args, **kwargs)
    
    @action(
        detail=False,
        methods=['post'],
        permission_classes=[IsTeacher],
        parser_classes=[MultiPartParser, FormParser],
        url_path='process-classroom-image',
        url_name='process-classroom-image'
    )
    def process_classroom_image(self, request):
        """
        Process classroom image for batch face recognition attendance.
        Updates existing absent→present records for recognised students.

        POST /api/attendance/process-classroom-image/
        Body (multipart/form-data):
          - session_id: Active attendance session ID (required)
          - image: Image file from classroom camera
        """
        user = request.user
        if not user.is_teacher():
            return Response(
                {'success': False, 'message': str(MSG_INSTRUCTOR_ONLY), 'error': 'permission_denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        session_id = request.data.get('session_id')
        image_file = request.FILES.get('image')
        
        if not session_id:
            return Response(
                {'success': False, 'message': str(MSG_SESSION_ID_REQUIRED), 'error': 'missing_session_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not image_file:
            return Response(
                {'success': False, 'message': str(MSG_IMAGE_FILE_REQUIRED), 'error': 'missing_image'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get active session (allow admin to process any session)
        try:
            session = AttendanceSession.objects.get(id=session_id, status=AttendanceSession.ACTIVE)
        except AttendanceSession.DoesNotExist:
            return Response(
                {'success': False, 'message': str(MSG_ACTIVE_SESSION_NOT_FOUND).format(session_id=session_id), 'error': 'session_not_found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Teachers can only process their own sessions
        if user.is_teacher():
            teacher = getattr(user, 'teacher_profile', None)
            if session.instructor and teacher and session.instructor != teacher:
                return Response(
                    {'success': False, 'message': str(MSG_ONLY_OWN_SESSIONS), 'error': 'permission_denied'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # ── Class-based student filtering ──
        # Collect the student IDs that belong to the session's class so the
        # face recognition service only matches against those students.
        # This prevents false-positive matches on students from other classes.
        session_class = session.school_class
        class_student_ids = []
        if session_class:
            class_student_ids = list(
                session_class.students.values_list('student_id', flat=True)
            )

        client = get_face_recognition_client()
        image_file.seek(0)
        detection_result = client.detect_faces_batch(
            image_file,
            tolerance=0.6,
            model='hog',
            num_jitters=1,
            student_ids=class_student_ids if class_student_ids else None,
        )
        
        if not detection_result.get('success'):
            return Response(
                {
                    'success': False,
                    'message': detection_result.get('message', str(MSG_FACE_DETECTION_FAILED)),
                    'error': detection_result.get('error', 'detection_failed')
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        matches = detection_result.get('matches', [])
        today = date.today()
        updated_records = []
        matched_students = []
        
        skipped_mismatch = []  # students recognised but not in this class

        for match in matches:
            if not match.get('match'):
                continue
            
            student_id_str = match.get('student_id')
            if not student_id_str:
                continue
            
            from django.db.models import Q
            try:
                query = Q(student_id=student_id_str) | Q(user__username=student_id_str)
                if student_id_str.isdigit():
                    query |= Q(id=int(student_id_str))
                student = Student.objects.filter(query).first()
                if not student:
                    continue
            except Exception:
                continue
            
            # ── Class verification: only mark attendance for students
            # belonging to the session's assigned class ──
            if session_class and student.school_class_id != session_class.id:
                skipped_mismatch.append({
                    'student_id': student_id_str,
                    'student_name': student.user.get_full_name() or student_id_str,
                    'matched_class': str(student.school_class) if student.school_class else None,
                    'session_class': str(session_class),
                    'confidence': match.get('confidence', 0),
                })
                continue

            confidence = match.get('confidence', 0)

            # Always update/create: set status to present
            att, created = Attendance.objects.get_or_create(
                student=student,
                date=today,
                defaults={
                    'status': Attendance.PRESENT,
                    'source': Attendance.FACE_RECOGNITION,
                    'session': session,
                    'notes': f'Recognised via face recognition. Confidence: {confidence:.2f}%',
                }
            )
            if not created:
                # Update existing record to present
                att.status = Attendance.PRESENT
                att.source = Attendance.FACE_RECOGNITION
                att.session = session
                att.notes = f'Recognised via face recognition. Confidence: {confidence:.2f}%'
                att.save()

            updated_records.append(att)
            matched_students.append(student_id_str)
        
        # Update session statistics
        session.total_faces_detected += detection_result.get('num_faces_detected', 0)
        session.total_matches += len(matched_students)
        session.total_attendance_marked = session.attendances.filter(status=Attendance.PRESENT).count()
        session.save()

        # Return updated full roster so frontend can refresh lists
        roster = _build_roster(session)
        
        return Response(
            {
                'success': True,
                'session_id': session.id,
                'num_faces_detected': detection_result.get('num_faces_detected', 0),
                'num_matches': len(matched_students),
                'matched_students': matched_students,
                'skipped_class_mismatch': skipped_mismatch,
                'matches': matches,
                'roster': roster,
                'num_attendance_marked': session.total_attendance_marked,
                'message': str(MSG_PROCESSING_RESULT).format(faces=detection_result.get("num_faces_detected", 0), records=len(updated_records)),
            },
            status=status.HTTP_200_OK
        )


def _build_roster(session):
    """Return present/absent lists for a session."""
    records = session.attendances.select_related('student__user').all()
    present = []
    absent = []
    for att in records:
        entry = {
            'id': att.id,
            'student_db_id': att.student_id,
            'student_id': att.student.student_id,
            'student_name': att.student.user.get_full_name() or att.student.student_id,
            'status': att.status,
            'source': att.source,
        }
        if att.status == Attendance.PRESENT:
            present.append(entry)
        else:
            absent.append(entry)
    return {'present': present, 'absent': absent}


class AttendanceSessionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Attendance Session management.
    - Teachers: can create, complete, cancel sessions and manage attendance.
    - Admins: can only view/list sessions and session history (read-only).
    """
    queryset = AttendanceSession.objects.all()
    serializer_class = AttendanceSessionSerializer
    permission_classes = [IsAdminOrTeacher]

    def get_permissions(self):
        """Override permissions based on action.
        Write operations (create, update, destroy, complete, cancel) are teacher-only.
        Read operations (list, retrieve, active, roster, history) allow admin + teacher.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy',
                           'complete_session', 'cancel_session']:
            return [IsTeacher()]
        # All other actions (list, retrieve, active_session, roster,
        # session_history, class_session_history) → admin + teacher
        return [IsAdminOrTeacher()]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin():
            return AttendanceSession.objects.all()
        elif user.is_teacher():
            if hasattr(user, 'teacher_profile'):
                return AttendanceSession.objects.filter(instructor=user.teacher_profile)
            return AttendanceSession.objects.none()
        return AttendanceSession.objects.none()
    
    def perform_create(self, serializer):
        """
        Auto-set instructor, date=today, status=active on create.
        Bulk-creates absent attendance records for all students in the selected class.
        Prevents duplicate active sessions for the same class+date.
        """
        user = self.request.user
        today = date.today()
        class_name = serializer.validated_data.get('class_name', '')
        school_class = serializer.validated_data.get('school_class', None)

        instructor = getattr(user, 'teacher_profile', None)

        # Prevent duplicate active sessions for same class+date
        dup_qs = AttendanceSession.objects.filter(
            date=today,
            status=AttendanceSession.ACTIVE,
            class_name=class_name,
        )
        duplicate = dup_qs.first()
        if duplicate:
            raise serializers.ValidationError(
                str(MSG_DUPLICATE_ACTIVE_SESSION).format(class_name=class_name, session_id=duplicate.id)
            )

        save_kwargs = dict(date=today, status=AttendanceSession.ACTIVE)
        if instructor:
            save_kwargs['instructor'] = instructor

        session = serializer.save(**save_kwargs)

        # Ensure every student in the class has an attendance record linked to
        # this session.  If a record already exists for today (e.g. from a
        # previous/cancelled session or manual entry), link it to the NEW
        # session so the roster & counts are correct.  Otherwise create a new
        # absent record.
        if school_class:
            students = list(school_class.students.all())
        else:
            students = []

        new_records = []
        existing_to_link = []
        for student in students:
            existing = Attendance.objects.filter(student=student, date=today).first()
            if existing:
                # Link the existing record to this session (keep its status)
                existing.session = session
                existing_to_link.append(existing)
            else:
                new_records.append(Attendance(
                    student=student,
                    date=today,
                    status=Attendance.ABSENT,
                    source=Attendance.MANUAL,
                    session=session,
                    notes='Auto-created as absent at session start',
                ))
        if new_records:
            # bulk_create bypasses model.save() validation; safe here since we checked uniqueness
            Attendance.objects.bulk_create(new_records)
        if existing_to_link:
            Attendance.objects.bulk_update(existing_to_link, ['session'])

        # Update count
        session.total_attendance_marked = session.attendances.filter(status=Attendance.PRESENT).count()
        session.save(update_fields=['total_attendance_marked'])

    @action(detail=False, methods=['get'], url_path='active', url_name='active-session')
    def active_session(self, request):
        """GET /api/attendance-sessions/active/"""
        qs = self.get_queryset().filter(status=AttendanceSession.ACTIVE)
        session = qs.order_by('-started_at').first()
        if not session:
            return Response({'active': False, 'session': None}, status=status.HTTP_200_OK)
        serializer = self.get_serializer(session)
        return Response({'active': True, 'session': serializer.data}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='roster', url_name='session-roster')
    def roster(self, request, pk=None):
        """
        GET /api/attendance-sessions/{id}/roster/
        Returns present and absent student lists for a session.
        """
        session = self.get_object()
        return Response(_build_roster(session), status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='complete', url_name='complete-session')
    def complete_session(self, request, pk=None):
        """Complete an active attendance session"""
        session = self.get_object()
        if session.status != AttendanceSession.ACTIVE:
            return Response(
                {'success': False, 'message': str(MSG_SESSION_NOT_ACTIVE).format(status=session.get_status_display()), 'error': 'invalid_status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        session.complete()

        # Send absence notifications to parents (create_notification handles dedupe + MSSQL)
        absent_records = session.attendances.filter(status=Attendance.ABSENT).select_related('student__parent__user', 'student__user')
        for att in absent_records:
            student = att.student
            parent = getattr(student, 'parent', None)
            if parent and getattr(parent, 'user_id', None):
                student_name = student.user.get_full_name() or student.student_id
                notification_services.create_notification(
                    recipient=parent.user,
                    notification_type=Notification.Type.ATTENDANCE,
                    title_en="Absence Alert",
                    title_ar="تنبيه غياب",
                    body_en=f"Your child {student_name} was absent today.",
                    body_ar=f"تغيّب {student_name} اليوم.",
                    dedupe_key=f"att_session_{session.id}_absent_{student.id}",
                    metadata={
                        "session_id": session.id,
                        "student_id": student.id,
                        "date": str(session.date),
                    },
                    student=student,
                )

        return Response({'success': True, 'message': str(MSG_SESSION_COMPLETED), 'session': self.get_serializer(session).data})

    @action(detail=True, methods=['post'], url_path='cancel', url_name='cancel-session')
    def cancel_session(self, request, pk=None):
        """Cancel an active attendance session"""
        session = self.get_object()
        if session.status != AttendanceSession.ACTIVE:
            return Response(
                {'success': False, 'message': str(MSG_SESSION_NOT_ACTIVE).format(status=session.get_status_display()), 'error': 'invalid_status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        session.cancel()
        return Response({'success': True, 'message': str(MSG_SESSION_CANCELLED), 'session': self.get_serializer(session).data})

    @action(detail=True, methods=['get'], url_path='history', url_name='session-history')
    def session_history(self, request, pk=None):
        """
        GET /api/attendance-sessions/{id}/history/

        Returns a comprehensive view of all students in the session's class,
        showing who was marked present, absent, or not yet marked.

        This is different from the roster endpoint which only returns students
        that have attendance records. The history endpoint includes ALL students
        enrolled in the class, even those without any attendance record.
        """
        session = self.get_object()
        school_class = session.school_class

        if not school_class:
            return Response(
                {
                    'success': False,
                    'message': 'This session is not linked to a class. Cannot show student history.',
                    'error': 'no_class_linked',
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # All students enrolled in the class
        all_students = list(
            school_class.students.select_related('user', 'parent__user').all()
        )

        # Attendance records for this session
        attendance_records = {
            att.student_id: att
            for att in session.attendances.select_related('student__user').all()
        }

        students_data = []
        present_count = 0
        absent_count = 0
        not_marked_count = 0

        for student in all_students:
            att = attendance_records.get(student.id)

            if att:
                if att.status == Attendance.PRESENT:
                    present_count += 1
                    student_status = Attendance.PRESENT
                    status_display = 'Present'
                else:
                    absent_count += 1
                    student_status = Attendance.ABSENT
                    status_display = 'Absent'
                students_data.append({
                    'student_db_id': student.id,
                    'student_id': student.student_id or '',
                    'student_name': student.user.get_full_name() or student.student_id or '',
                    'attendance_id': att.id,
                    'status': student_status,
                    'status_display': status_display,
                    'source': att.source,
                    'source_display': att.get_source_display(),
                    'notes': att.notes,
                    'marked_at': att.updated_at,
                })
            else:
                not_marked_count += 1
                students_data.append({
                    'student_db_id': student.id,
                    'student_id': student.student_id or '',
                    'student_name': student.user.get_full_name() or student.student_id or '',
                    'attendance_id': None,
                    'status': 'not_marked',
                    'status_display': 'Not Marked',
                    'source': None,
                    'source_display': None,
                    'notes': None,
                    'marked_at': None,
                })

        result = {
            'session': AttendanceSessionSerializer(session).data,
            'total_class_students': len(all_students),
            'present_count': present_count,
            'absent_count': absent_count,
            'not_marked_count': not_marked_count,
            'students': students_data,
        }

        return Response(result, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='class-history', url_name='class-session-history')
    def class_session_history(self, request):
        """
        GET /api/attendance-sessions/class-history/?school_class=<class_id>&status=completed

        Returns sessions for a given class, each with the full student attendance
        breakdown (present, absent, not_marked).

        Query params:
          - school_class (required): class ID
          - status (optional): filter by session status (active, completed, cancelled).
            Defaults to showing completed + cancelled sessions.
            Pass "all" to include every status.

        Useful for viewing historical attendance records for a class over time.
        """
        school_class_id = request.query_params.get('school_class')

        if not school_class_id:
            return Response(
                {
                    'success': False,
                    'message': 'school_class query parameter is required.',
                    'error': 'missing_school_class',
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify the class exists
        from classes.models import SchoolClass
        try:
            school_class = SchoolClass.objects.get(pk=school_class_id)
        except SchoolClass.DoesNotExist:
            return Response(
                {
                    'success': False,
                    'message': f'Class with id {school_class_id} does not exist.',
                    'error': 'class_not_found',
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # Status filter
        status_filter = request.query_params.get('status', '')
        if status_filter == 'all':
            sessions_qs = self.get_queryset().filter(
                school_class_id=school_class_id,
            ).order_by('-date', '-started_at')
        elif status_filter in [AttendanceSession.ACTIVE, AttendanceSession.COMPLETED, AttendanceSession.CANCELLED]:
            sessions_qs = self.get_queryset().filter(
                school_class_id=school_class_id,
                status=status_filter,
            ).order_by('-date', '-started_at')
        else:
            # Default: completed + cancelled
            sessions_qs = self.get_queryset().filter(
                school_class_id=school_class_id,
                status__in=[AttendanceSession.COMPLETED, AttendanceSession.CANCELLED],
            ).order_by('-date', '-completed_at')

        # All students in the class (single query, reused for every session)
        all_students = list(
            school_class.students.select_related('user', 'parent__user').all()
        )

        results = []
        for session in sessions_qs:
            attendance_records = {
                att.student_id: att
                for att in session.attendances.select_related('student__user').all()
            }

            students_data = []
            present_count = 0
            absent_count = 0
            not_marked_count = 0

            for student in all_students:
                att = attendance_records.get(student.id)

                if att:
                    if att.status == Attendance.PRESENT:
                        present_count += 1
                        student_status = Attendance.PRESENT
                        status_display = 'Present'
                    else:
                        absent_count += 1
                        student_status = Attendance.ABSENT
                        status_display = 'Absent'
                    students_data.append({
                        'student_db_id': student.id,
                        'student_id': student.student_id or '',
                        'student_name': student.user.get_full_name() or student.student_id or '',
                        'attendance_id': att.id,
                        'status': student_status,
                        'status_display': status_display,
                        'source': att.source,
                        'source_display': att.get_source_display(),
                        'notes': att.notes,
                        'marked_at': att.updated_at,
                    })
                else:
                    not_marked_count += 1
                    students_data.append({
                        'student_db_id': student.id,
                        'student_id': student.student_id or '',
                        'student_name': student.user.get_full_name() or student.student_id or '',
                        'attendance_id': None,
                        'status': 'not_marked',
                        'status_display': 'Not Marked',
                        'source': None,
                        'source_display': None,
                        'notes': None,
                        'marked_at': None,
                    })

            results.append({
                'session': AttendanceSessionSerializer(session).data,
                'total_class_students': len(all_students),
                'present_count': present_count,
                'absent_count': absent_count,
                'not_marked_count': not_marked_count,
                'students': students_data,
            })

        return Response({
            'school_class_id': int(school_class_id),
            'school_class_name': school_class.display_name or school_class.name,
            'total_sessions': len(results),
            'sessions': results,
        }, status=status.HTTP_200_OK)
