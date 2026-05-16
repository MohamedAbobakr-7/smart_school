from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', _('Admin')
        TEACHER = 'TEACHER', _('Teacher')
        STUDENT = 'STUDENT', _('Student')
        PARENT = 'PARENT', _('Parent')

    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.STUDENT,
        help_text='User role for access control'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Automatically set role to ADMIN for superusers
        if self.is_superuser and self.role != self.Role.ADMIN:
            self.role = self.Role.ADMIN
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['role']),
        ]

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    # Role check methods
    def is_admin(self):
        """Check if user has ADMIN role"""
        return self.role == self.Role.ADMIN

    def is_teacher(self):
        """Check if user has TEACHER role"""
        return self.role == self.Role.TEACHER

    def is_student(self):
        """Check if user has STUDENT role"""
        return self.role == self.Role.STUDENT

    def is_parent(self):
        """Check if user has PARENT role"""
        return self.role == self.Role.PARENT

    def has_role(self, *roles):
        """Check if user has any of the specified roles"""
        return self.role in roles

    def has_any_admin_or_teacher(self):
        """Check if user is ADMIN or TEACHER"""
        return self.role in [self.Role.ADMIN, self.Role.TEACHER]

