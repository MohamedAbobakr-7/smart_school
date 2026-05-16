from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class Attendance(models.Model):
    """
    Attendance model representing student attendance records.
    
    Relationships:
    - student: Foreign key to Student (each attendance record belongs to one student)
    - marked_by: Foreign key to Teacher (optional, who marked the attendance)
    
    Constraints:
    - Unique together: (student, date) - ensures no duplicate attendance per student per day
    """
    
    # Status choices
    PRESENT = 'present'
    ABSENT = 'absent'
    
    STATUS_CHOICES = [
        (PRESENT, _('Present')),
        (ABSENT, _('Absent')),
    ]
    
    # Source choices
    MANUAL = 'manual'
    FACE_RECOGNITION = 'face_recognition'
    
    SOURCE_CHOICES = [
        (MANUAL, _('Manual')),
        (FACE_RECOGNITION, _('Face Recognition')),
    ]
    
    # Relationship to Student
    # Each attendance record belongs to one student
    # If student is deleted, attendance records are also deleted (CASCADE)
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='attendances',
        help_text='Student for this attendance record'
    )
    
    # Date of attendance
    date = models.DateField(
        help_text='Date of attendance'
    )
    
    # Attendance status
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=PRESENT,
        help_text='Attendance status: Present or Absent'
    )
    
    # Source of attendance record
    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default=MANUAL,
        help_text='Source of attendance: Manual entry or Face Recognition'
    )
    
    # Optional fields
    notes = models.TextField(
        blank=True,
        help_text='Additional notes about the attendance'
    )
    
    # Who marked the attendance (optional)
    marked_by = models.ForeignKey(
        'teachers.Teacher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='marked_attendances',
        help_text='Teacher who marked this attendance (if manual)'
    )
    
    # Reference to attendance session (if created via face recognition session)
    session = models.ForeignKey(
        'AttendanceSession',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='attendances',
        help_text='Attendance session this record belongs to'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'attendance'
        verbose_name = 'Attendance'
        verbose_name_plural = 'Attendances'
        ordering = ['-date', 'student']
        # Ensure no duplicate attendance per student per day
        unique_together = [['student', 'date']]
        indexes = [
            models.Index(fields=['student', 'date']),
            models.Index(fields=['date']),
            models.Index(fields=['status']),
            models.Index(fields=['source']),
            models.Index(fields=['session']),
        ]

    def __str__(self):
        return f"{self.student.student_id} - {self.date} - {self.get_status_display()} ({self.get_source_display()})"
    
    def clean(self):
        """Validate the attendance record"""
        super().clean()
        from smartSchool.messages import MSG_ATTENDANCE_DUPLICATE_MODEL
        
        # Check for duplicate attendance on the same date for the same student
        if self.pk is None:  # New record
            if Attendance.objects.filter(student=self.student, date=self.date).exists():
                raise ValidationError(
                    str(MSG_ATTENDANCE_DUPLICATE_MODEL).format(student_id=self.student.student_id, date=self.date)
                )
    
    def save(self, *args, **kwargs):
        """Override save to call clean validation"""
        self.full_clean()
        super().save(*args, **kwargs)


class AttendanceSession(models.Model):
    """
    Attendance session model for instructor-controlled face recognition attendance.
    
    Instructors start a session, capture images from classroom camera,
    and the system automatically detects faces and marks attendance.
    """
    
    # Session status choices
    ACTIVE = 'active'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'
    
    STATUS_CHOICES = [
        (ACTIVE, _('Active')),
        (COMPLETED, _('Completed')),
        (CANCELLED, _('Cancelled')),
    ]
    
    # Instructor who started the session
    instructor = models.ForeignKey(
        'teachers.Teacher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='attendance_sessions',
        help_text='Instructor who started this attendance session (null for admin-created sessions)'
    )
    
    # Session date
    date = models.DateField(
        help_text='Date of the attendance session'
    )
    
    # Session status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=ACTIVE,
        help_text='Current status of the session'
    )
    
    # Session metadata
    class_name = models.CharField(
        max_length=100,
        blank=True,
        help_text='Class or subject name for this session'
    )
    
    # Link to the SchoolClass so we can fetch enrolled students
    school_class = models.ForeignKey(
        'classes.SchoolClass',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='attendance_sessions',
        help_text='Class whose students are tracked in this session'
    )

    notes = models.TextField(
        blank=True,
        help_text='Additional notes about the session'
    )
    
    # Statistics
    total_faces_detected = models.IntegerField(
        default=0,
        help_text='Total number of faces detected across all images'
    )
    
    total_matches = models.IntegerField(
        default=0,
        help_text='Total number of successful face matches'
    )
    
    total_attendance_marked = models.IntegerField(
        default=0,
        help_text='Total number of attendance records created'
    )
    
    # Timestamps
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'attendance_sessions'
        verbose_name = 'Attendance Session'
        verbose_name_plural = 'Attendance Sessions'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['instructor', 'date']),
            models.Index(fields=['status']),
            models.Index(fields=['date']),
        ]

    def __str__(self):
        instructor_label = self.instructor.teacher_id if self.instructor_id else 'admin'
        return f"Session {self.id} - {instructor_label} - {self.date} ({self.get_status_display()})"
    
    def complete(self):
        """Mark session as completed"""
        from django.utils import timezone
        self.status = self.COMPLETED
        self.completed_at = timezone.now()
        self.save()
    
    def cancel(self):
        """Cancel the session"""
        from django.utils import timezone
        self.status = self.CANCELLED
        self.completed_at = timezone.now()
        self.save()

