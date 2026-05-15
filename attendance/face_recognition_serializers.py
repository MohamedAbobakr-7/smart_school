"""
Serializers for Face Recognition Attendance
"""

from rest_framework import serializers


class FaceRecognitionAttendanceSerializer(serializers.Serializer):
    """Serializer for face recognition attendance request"""
    
    student_id = serializers.CharField(
        required=True,
        help_text="Student ID to verify and mark attendance for"
    )
    
    # Image will be handled as a file upload in the view
    # No need to define it here as it's handled via request.FILES


class FaceRecognitionAttendanceResponseSerializer(serializers.Serializer):
    """Serializer for face recognition attendance response"""
    
    success = serializers.BooleanField()
    attendance_id = serializers.IntegerField(required=False, allow_null=True)
    student_id = serializers.CharField()
    date = serializers.DateField(required=False, allow_null=True)
    match = serializers.BooleanField()
    confidence = serializers.FloatField(required=False, allow_null=True)
    message = serializers.CharField()
    error = serializers.CharField(required=False, allow_null=True)
    attendance = serializers.DictField(required=False, allow_null=True)

