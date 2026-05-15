from django.db import models
from django.conf import settings
from django.db.models.signals import post_delete
from django.dispatch import receiver
import os


class Student(models.Model):
    """
    Student model representing a student in the school system.
    
    Relationships:
    - user: One-to-one relationship with User (each student has one user account)
    - parent: Foreign key to Parent (a student can have one parent/guardian)
    """
    
    # One-to-one relationship with User model
    # Each student has exactly one user account
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_profile',
        help_text='User account associated with this student'
    )
    
    # Student identification
    student_id = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        default=None,
        help_text='Unique identifier for the student. Auto-generated if left blank.'
    )
    
    # Personal information
    date_of_birth = models.DateField(
        null=True,
        blank=True,
        help_text='Student date of birth'
    )

    # Profile / face photo – used for face recognition attendance
    photo = models.ImageField(
        upload_to='student_photos/',
        null=True,
        blank=True,
        help_text='Clear face photo used for attendance face recognition'
    )

    # Face registration status (set by backend after encoding is stored)
    face_registered = models.BooleanField(
        default=False,
        help_text='True when a face encoding has been successfully registered in the face recognition service'
    )
    
    # Class/Level information
    class_level = models.CharField(
        max_length=50,
        blank=True,
        help_text='Current class level (e.g., Grade 1, Grade 2, Form 1, etc.)'
    )
    class_id = models.CharField(
        max_length=50,
        blank=True,
        help_text='Class identifier (e.g., G10-A, CLASS-01)'
    )

    # Structured FK link to SchoolClass
    school_class = models.ForeignKey(
        'classes.SchoolClass',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students',
        help_text='Assigned class group for this student'
    )
    
    # Relationship to Parent
    # A student can have one parent/guardian
    # If parent is deleted, set to NULL (student remains but parent reference is removed)
    parent = models.ForeignKey(
        'parents.Parent',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        help_text='Parent or guardian of this student'
    )
    subjects = models.ManyToManyField(
        'subjects.Subject',
        blank=True,
        related_name='enrolled_students',
        help_text='Subjects this student is enrolled in'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'students'
        verbose_name = 'Student'
        verbose_name_plural = 'Students'
        ordering = ['student_id']
        indexes = [
            models.Index(fields=['student_id']),
            models.Index(fields=['class_level']),
            models.Index(fields=['class_id']),
            models.Index(fields=['parent']),
        ]

    def __str__(self):
        return f"{self.student_id} - {self.user.get_full_name() or self.user.username}"


@receiver(post_delete, sender=Student)
def auto_delete_photo_on_delete(sender, instance, **kwargs):
    """
    Deletes photo from filesystem
    when corresponding `Student` object is deleted.
    """
    if instance.photo:
        if os.path.isfile(instance.photo.path):
            os.remove(instance.photo.path)

