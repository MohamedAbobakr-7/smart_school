from django.db import models
from django.db.models.signals import post_delete
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

