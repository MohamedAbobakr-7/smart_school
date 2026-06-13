"""
Signals for the attendance app.

Whenever an Attendance record is created, updated, or deleted,
refresh the linked session's total_attendance_marked counter
so it stays accurate even for manual attendance entries.
"""
from django.db.models.signals import post_save, post_delete
from django.db.transaction import on_commit


def _refresh_session_marked_count(att):
    """Re-count present attendances on the linked session and save."""
    session = att.session
    if session is None:
        return
    session.total_attendance_marked = session.attendances.filter(
        status='present'
    ).count()
    session.save(update_fields=['total_attendance_marked'])


def _refresh_on_save(sender, instance, **kwargs):
    """post_save handler — refresh session count after any attendance change."""
    # Use on_commit so the count is refreshed after the current transaction
    # finishes (avoids counting stale data inside bulk_create transactions).
    on_commit(lambda: _refresh_session_marked_count(instance))


def _refresh_on_delete(sender, instance, **kwargs):
    """post_delete handler — refresh session count after an attendance delete."""
    on_commit(lambda: _refresh_session_marked_count(instance))
