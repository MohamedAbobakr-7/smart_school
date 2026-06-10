from django.db import models
from django.db.models.signals import post_delete, m2m_changed
from django.dispatch import receiver
import os


class Subject(models.Model):
    """
    Subject model representing a subject/course in the school system.
    
    Relationships:
    - teachers: Many-to-many relationship with Teacher (a subject can be taught by multiple teachers)
                 This is the reverse relationship from Teacher.assigned_subjects
    """
    
    # Subject identification
    name = models.CharField(
        max_length=100,
        help_text='Name of the subject (e.g., Mathematics, English, Science)'
    )
    
    code = models.CharField(
        max_length=20,
        unique=True,
        help_text='Unique code for the subject (e.g., MATH101, ENG201)'
    )
    
    description = models.TextField(
        blank=True,
        help_text='Description of the subject'
    )
    
    # Many-to-many relationship with Teacher
    # A subject can be taught by multiple teachers, and a teacher can teach multiple subjects
    # This is accessed via Teacher.assigned_subjects (reverse relationship)
    # To access teachers for a subject: subject.teachers.all()
    # To access subjects for a teacher: teacher.assigned_subjects.all()
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'subjects'
        verbose_name = 'Subject'
        verbose_name_plural = 'Subjects'
        ordering = ['name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def get_teachers_list(self):
        """Get a list of teacher names assigned to this subject"""
        return [teacher.user.get_full_name() or teacher.user.username for teacher in self.teachers.all()]
    
    def get_teachers_count(self):
        """Get the number of teachers assigned to this subject"""
        return self.teachers.count()


def material_upload_to(instance, filename):
    return f"materials/{instance.subject_id or 'general'}/{filename}"


class Material(models.Model):
    """
    Educational material (PDF, DOCX, etc.) uploaded by a teacher for a subject.
    """
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='materials'
    )
    
    target_classes = models.ManyToManyField(
        'classes.SchoolClass',
        related_name='materials',
        help_text='Target classes for this educational material.',
    )
    
    uploaded_by = models.ForeignKey(
        'teachers.Teacher',
        on_delete=models.CASCADE,
        related_name='uploaded_materials'
    )
    
    file = models.FileField(upload_to=material_upload_to)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'materials'
        verbose_name = 'Material'
        verbose_name_plural = 'Materials'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['subject']),
            models.Index(fields=['uploaded_by']),
        ]

    def __str__(self):
        return f"{self.title} ({self.subject.code})"


@receiver(post_delete, sender=Material)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes file from filesystem
    when corresponding `Material` object is deleted.
    """
    if instance.file:
        if os.path.isfile(instance.file.path):
            os.remove(instance.file.path)


class SubjectEnrollment(models.Model):
    """
    Through-model that tracks a student's enrollment in a subject
    with metadata such as status, academic year, and dates.

    This model is kept in sync with the Student.subjects M2M field via signals.
    When a SubjectEnrollment with status=ACTIVE is created, the subject is
    automatically added to Student.subjects. When the enrollment is withdrawn
    or deleted, the subject is removed from Student.subjects.
    """

    STATUS_ACTIVE = 'ACTIVE'
    STATUS_WITHDRAWN = 'WITHDRAWN'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_SUSPENDED = 'SUSPENDED'

    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_WITHDRAWN, 'Withdrawn'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_SUSPENDED, 'Suspended'),
    ]

    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='subject_enrollments',
        help_text='The student enrolled in the subject',
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='enrollments',
        help_text='The subject the student is enrolled in',
    )
    school_class = models.ForeignKey(
        'classes.SchoolClass',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subject_enrollments',
        help_text='The class/grade group at the time of enrollment',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE,
        help_text='Current enrollment status',
    )
    enrollment_date = models.DateField(
        auto_now_add=True,
        help_text='Date when the enrollment was created',
    )
    withdrawal_date = models.DateField(
        null=True,
        blank=True,
        help_text='Date when the student withdrew (set automatically on WITHDRAWN)',
    )
    academic_year = models.CharField(
        max_length=20,
        blank=True,
        default='',
        help_text='Academic year label (e.g., 2025-2026)',
    )
    notes = models.TextField(
        blank=True,
        default='',
        help_text='Optional notes about this enrollment',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'subject_enrollments'
        verbose_name = 'Subject Enrollment'
        verbose_name_plural = 'Subject Enrollments'
        ordering = ['student', 'subject']
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'subject', 'academic_year'],
                name='uniq_student_subject_academic_year',
                condition=models.Q(academic_year__gt=''),
            ),
            models.UniqueConstraint(
                fields=['student', 'subject'],
                name='uniq_student_subject_no_year',
                condition=models.Q(academic_year=''),
            ),
        ]
        indexes = [
            models.Index(fields=['student']),
            models.Index(fields=['subject']),
            models.Index(fields=['school_class']),
            models.Index(fields=['status']),
            models.Index(fields=['academic_year']),
        ]

    def __str__(self):
        return f"{self.student} → {self.subject} ({self.status})"

    def save(self, *args, **kwargs):
        # Auto-set withdrawal_date when status changes to WITHDRAWN
        if self.status == self.STATUS_WITHDRAWN and not self.withdrawal_date:
            from datetime import date
            self.withdrawal_date = date.today()
        # Clear withdrawal_date if re-activated
        if self.status == self.STATUS_ACTIVE and self.withdrawal_date:
            self.withdrawal_date = None
        super().save(*args, **kwargs)


# ── Signal: sync SubjectEnrollment ↔ Student.subjects M2M ──────────────

# Module-level flag to prevent infinite signal loops
_syncing_enrollment = False


def _set_syncing_flag(value):
    """Set the module-level syncing flag (used by views to avoid double-sync)."""
    global _syncing_enrollment
    _syncing_enrollment = value


@receiver(m2m_changed, sender='students.Student_subjects')
def sync_enrollment_from_m2m(action, instance, pk_set, **kwargs):
    """
    When subjects are added/removed via the Student.subjects M2M field
    (e.g. through StudentSerializer), create or update SubjectEnrollment records.
    """
    global _syncing_enrollment
    if _syncing_enrollment:
        return  # avoid infinite loop

    if action == 'post_add' and pk_set:
        for subject_pk in pk_set:
            SubjectEnrollment.objects.get_or_create(
                student=instance,
                subject_id=subject_pk,
                school_class=instance.school_class,
                defaults={'status': SubjectEnrollment.STATUS_ACTIVE},
            )

    elif action == 'post_remove' and pk_set:
        for subject_pk in pk_set:
            SubjectEnrollment.objects.filter(
                student=instance,
                subject_id=subject_pk,
                status=SubjectEnrollment.STATUS_ACTIVE,
            ).update(status=SubjectEnrollment.STATUS_WITHDRAWN)

    elif action == 'post_clear':
        SubjectEnrollment.objects.filter(
            student=instance,
            status=SubjectEnrollment.STATUS_ACTIVE,
        ).update(status=SubjectEnrollment.STATUS_WITHDRAWN)


@receiver([models.signals.post_save, models.signals.post_delete], sender=SubjectEnrollment)
def sync_m2m_from_enrollment(sender, instance, **kwargs):
    """
    When a SubjectEnrollment is saved or deleted, sync the Student.subjects M2M.
    - ACTIVE enrollment → add subject to M2M
    - WITHDRAWN/COMPLETED/SUSPENDED → remove subject from M2M
    - Deleted enrollment → remove subject from M2M
    """
    global _syncing_enrollment
    if _syncing_enrollment:
        return  # avoid infinite loop

    _syncing_enrollment = True
    try:
        student = instance.student
        subject = instance.subject

        if kwargs.get('created') or instance.status == SubjectEnrollment.STATUS_ACTIVE:
            student.subjects.add(subject)
        else:
            # WITHDRAWN, COMPLETED, SUSPENDED, or deleted
            student.subjects.remove(subject)
    finally:
        _syncing_enrollment = False

