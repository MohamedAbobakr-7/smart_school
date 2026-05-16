from rest_framework import serializers
from smartSchool.messages import MSG_ATTENDANCE_DUPLICATE
from .models import Attendance, AttendanceSession


class AttendanceSerializer(serializers.ModelSerializer):
    """Serializer for Attendance model"""
    
    # Display fields for related objects
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    student_id_display = serializers.CharField(source='student.student_id', read_only=True)
    marked_by_name = serializers.CharField(source='marked_by.user.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    source_display = serializers.CharField(source='get_source_display', read_only=True)
    session_id = serializers.IntegerField(source='session.id', read_only=True)
    
    class Meta:
        model = Attendance
        fields = [
            'id', 'student', 'student_id_display', 'student_name',
            'date', 'status', 'status_display',
            'source', 'source_display',
            'notes', 'marked_by', 'marked_by_name',
            'session', 'session_id',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, data):
        """Validate attendance data"""
        student = data.get('student')
        att_date = data.get('date')
        
        # Check for duplicate attendance (excluding current instance if updating)
        if student and att_date:
            existing = Attendance.objects.filter(student=student, date=att_date)
            if self.instance:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise serializers.ValidationError(
                    str(MSG_ATTENDANCE_DUPLICATE).format(date=att_date)
                )
        
        return data


class AttendanceSessionSerializer(serializers.ModelSerializer):
    """Serializer for AttendanceSession model"""
    
    instructor_name = serializers.SerializerMethodField()
    instructor_id = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    attendances_count = serializers.IntegerField(source='attendances.count', read_only=True)
    present_count = serializers.SerializerMethodField()
    absent_count = serializers.SerializerMethodField()
    school_class_name = serializers.SerializerMethodField()

    def get_instructor_name(self, obj):
        if obj.instructor:
            return obj.instructor.user.get_full_name()
        return None

    def get_instructor_id(self, obj):
        if obj.instructor:
            return obj.instructor.teacher_id
        return None

    def get_present_count(self, obj):
        return obj.attendances.filter(status=Attendance.PRESENT).count()

    def get_absent_count(self, obj):
        return obj.attendances.filter(status=Attendance.ABSENT).count()

    def get_school_class_name(self, obj):
        if obj.school_class:
            return obj.school_class.display_name or obj.school_class.name
        return None

    class Meta:
        model = AttendanceSession
        fields = [
            'id', 'instructor', 'instructor_id', 'instructor_name',
            'date', 'status', 'status_display',
            'class_name', 'school_class', 'school_class_name', 'notes',
            'total_faces_detected', 'total_matches', 'total_attendance_marked',
            'attendances_count', 'present_count', 'absent_count',
            'started_at', 'completed_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'instructor', 'date', 'status',
            'total_faces_detected', 'total_matches',
            'total_attendance_marked', 'started_at', 'completed_at', 'updated_at'
        ]
