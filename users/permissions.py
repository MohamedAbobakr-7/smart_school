"""
Permission utility functions for role-based access control.
"""
from rest_framework import permissions
from .models import User


class IsAdmin(permissions.BasePermission):
    """Permission class to check if user is ADMIN"""
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_admin()
        )


class IsTeacher(permissions.BasePermission):
    """Permission class to check if user is TEACHER"""
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_teacher()
        )


class IsStudent(permissions.BasePermission):
    """Permission class to check if user is STUDENT"""
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_student()
        )


class IsParent(permissions.BasePermission):
    """Permission class to check if user is PARENT"""
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_parent()
        )


class IsAdminOrTeacher(permissions.BasePermission):
    """Permission class to check if user is ADMIN or TEACHER"""
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.has_any_admin_or_teacher()
        )


class IsAdminOrOwner(permissions.BasePermission):
    """Permission class to check if user is ADMIN or owner of the object"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Admin has full access
        if request.user.is_admin():
            return True
        
        # Check if user is the owner
        # This assumes the object has a 'user' field
        # Override this method in views for custom ownership checks
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False


# Utility functions for permission checks
def is_admin(user):
    """Check if user is ADMIN"""
    return user and user.is_authenticated and user.is_admin()


def is_teacher(user):
    """Check if user is TEACHER"""
    return user and user.is_authenticated and user.is_teacher()


def is_student(user):
    """Check if user is STUDENT"""
    return user and user.is_authenticated and user.is_student()


def is_parent(user):
    """Check if user is PARENT"""
    return user and user.is_authenticated and user.is_parent()


def is_admin_or_teacher(user):
    """Check if user is ADMIN or TEACHER"""
    return user and user.is_authenticated and user.has_any_admin_or_teacher()


def has_role(user, *roles):
    """Check if user has any of the specified roles"""
    if not user or not user.is_authenticated:
        return False
    return user.has_role(*roles)


def can_access_student_data(user, student):
    """
    Check if user can access student data.
    - ADMIN: can access all
    - TEACHER: can access all
    - STUDENT: can only access their own data
    - PARENT: can access their children's data
    """
    if not user or not user.is_authenticated:
        return False
    
    if user.is_admin() or user.is_teacher():
        return True
    
    if user.is_student():
        # Check if student profile exists and matches
        if hasattr(user, 'student_profile'):
            return user.student_profile == student
        return False
    
    if user.is_parent():
        # Check if student is a child of this parent
        if hasattr(user, 'parent_profile') and student:
            return student.parent == user.parent_profile
        return False
    
    return False


def can_modify_student_data(user, student):
    """
    Check if user can modify student data.
    - ADMIN: can modify all
    - TEACHER: can modify all
    - STUDENT: cannot modify (read-only)
    - PARENT: can modify their children's data
    """
    if not user or not user.is_authenticated:
        return False
    
    if user.is_admin() or user.is_teacher():
        return True
    
    if user.is_student():
        return False  # Students cannot modify their own data
    
    if user.is_parent():
        # Check if student is a child of this parent
        if hasattr(user, 'parent_profile') and student:
            return student.parent == user.parent_profile
        return False
    
    return False

