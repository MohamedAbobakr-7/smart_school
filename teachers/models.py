from django.db import models
from django.conf import settings


class Teacher(models.Model):
    """
    Teacher model representing a teacher in the school system.
    
    Relationships:
    - user: One-to-one relationship with User (each teacher has one user account)
    - assigned_subjects: Many-to-many relationship with Subject (a teacher can teach multiple subjects)
    """
    
    # One-to-one relationship with User model
    # Each teacher has exactly one user account
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='teacher_profile',
        help_text='User account associated with this teacher'
    )
    
    # Teacher identification
    teacher_id = models.CharField(
        max_length=50,
        unique=True,
        help_text='Unique identifier for the teacher'
    )
    
    # Professional information
    hire_date = models.DateField(
        null=True,
        blank=True,
        help_text='Date when the teacher was hired'
    )
    
    # Many-to-many relationship with Subject
    # A teacher can teach multiple subjects, and a subject can be taught by multiple teachers
    assigned_subjects = models.ManyToManyField(
        'subjects.Subject',
        related_name='teachers',
        blank=True,
        help_text='Subjects assigned to this teacher'
    )

    # Classes this teacher is responsible for
    assigned_classes = models.ManyToManyField(
        'classes.SchoolClass',
        related_name='teachers',
        blank=True,
        help_text='Classes assigned to this teacher'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'teachers'
        verbose_name = 'Teacher'
        verbose_name_plural = 'Teachers'
        ordering = ['teacher_id']
        indexes = [
            models.Index(fields=['teacher_id']),
        ]

    def __str__(self):
        return f"{self.teacher_id} - {self.user.get_full_name() or self.user.username}"
    
    def get_subjects_list(self):
        """Get a list of subject names assigned to this teacher"""
        return [subject.name for subject in self.assigned_subjects.all()]

    def get_classes_list(self):
        """Get a list of unique class IDs assigned to this teacher"""
        return list(
            self.subject_class_relations.order_by('class_id')
            .values_list('class_id', flat=True)
            .distinct()
        )


class TeacherSubjectClass(models.Model):
    """
    Relation model that maps a teacher to a subject and class_id.
    """

    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name='subject_class_relations',
    )
    subject = models.ForeignKey(
        'subjects.Subject',
        on_delete=models.CASCADE,
        related_name='teacher_class_relations',
    )
    class_id = models.CharField(
        max_length=50,
        help_text='Class identifier (e.g., G10-A, CLASS-01)',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'teacher_subject_classes'
        verbose_name = 'Teacher Subject Class'
        verbose_name_plural = 'Teacher Subject Classes'
        ordering = ['teacher_id', 'subject_id', 'class_id']
        constraints = [
            models.UniqueConstraint(
                fields=['teacher', 'subject', 'class_id'],
                name='uniq_teacher_subject_class'
            )
        ]
        indexes = [
            models.Index(fields=['teacher']),
            models.Index(fields=['subject']),
            models.Index(fields=['class_id']),
        ]

    def __str__(self):
        return f"{self.teacher.teacher_id} / {self.subject.code} / {self.class_id}"

