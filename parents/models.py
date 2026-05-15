from django.db import models
from django.conf import settings


class Parent(models.Model):
    """
    Parent model representing a parent or guardian in the school system.
    
    Relationships:
    - user: One-to-one relationship with User (each parent has one user account)
    - children: Reverse relationship from Student model (a parent can have multiple children/students)
    """
    
    # One-to-one relationship with User model
    # Each parent has exactly one user account
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='parent_profile',
        help_text='User account associated with this parent'
    )
    
    # Parent identification
    parent_id = models.CharField(
        max_length=50,
        unique=True,
        help_text='Unique identifier for the parent'
    )
    
    # Personal information
    occupation = models.CharField(
        max_length=100,
        blank=True,
        help_text='Parent occupation'
    )
    
    relationship = models.CharField(
        max_length=50,
        blank=True,
        help_text='Relationship to student (e.g., Father, Mother, Guardian, etc.)'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'parents'
        verbose_name = 'Parent'
        verbose_name_plural = 'Parents'
        ordering = ['parent_id']
        indexes = [
            models.Index(fields=['parent_id']),
        ]

    def __str__(self):
        return f"{self.parent_id} - {self.user.get_full_name() or self.user.username}"
    
    @property
    def children(self):
        """
        Get all children (students) associated with this parent.
        This is a reverse relationship from Student.parent.
        """
        return self.children.all()
    
    def get_children_count(self):
        """Get the number of children (students) for this parent"""
        return self.children.count()
    
    def get_children_list(self):
        """Get a list of all children's names"""
        return [child.user.get_full_name() or child.user.username for child in self.children.all()]

