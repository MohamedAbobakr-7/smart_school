"""
Utility functions for user role-based access control.
These can be used in views, templates, or anywhere in the application.
"""
from .models import User


def check_user_role(user, required_role):
    """
    Check if a user has a specific role.
    
    Args:
        user: User instance
        required_role: One of User.Role values (ADMIN, TEACHER, STUDENT, PARENT)
    
    Returns:
        bool: True if user has the required role, False otherwise
    """
    if not user or not user.is_authenticated:
        return False
    return user.role == required_role


def require_role(*roles):
    """
    Decorator to require specific role(s) for a view function.
    
    Usage:
        @require_role(User.Role.ADMIN, User.Role.TEACHER)
        def my_view(request):
            ...
    """
    def decorator(func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                from django.http import HttpResponseForbidden
                return HttpResponseForbidden("Authentication required")
            
            if request.user.role not in roles:
                from django.http import HttpResponseForbidden
                return HttpResponseForbidden("Insufficient permissions")
            
            return func(request, *args, **kwargs)
        return wrapper
    return decorator


def get_users_by_role(role):
    """
    Get all users with a specific role.
    
    Args:
        role: One of User.Role values
    
    Returns:
        QuerySet: Users with the specified role
    """
    return User.objects.filter(role=role)


def is_admin_user(user):
    """Check if user is ADMIN"""
    return user and user.is_authenticated and user.is_admin()


def is_teacher_user(user):
    """Check if user is TEACHER"""
    return user and user.is_authenticated and user.is_teacher()


def is_student_user(user):
    """Check if user is STUDENT"""
    return user and user.is_authenticated and user.is_student()


def is_parent_user(user):
    """Check if user is PARENT"""
    return user and user.is_authenticated and user.is_parent()


def can_manage_users(user):
    """Check if user can manage other users (ADMIN only)"""
    return user and user.is_authenticated and user.is_admin()


def can_view_all_students(user):
    """Check if user can view all students (ADMIN, TEACHER)"""
    return user and user.is_authenticated and user.has_any_admin_or_teacher()


def can_edit_grades(user):
    """Check if user can edit grades (ADMIN, TEACHER)"""
    return user and user.is_authenticated and user.has_any_admin_or_teacher()


def can_view_attendance(user):
    """Check if user can view attendance (ADMIN, TEACHER, PARENT for their children)"""
    if not user or not user.is_authenticated:
        return False
    return user.is_admin() or user.is_teacher() or user.is_parent()

