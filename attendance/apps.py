from django.apps import AppConfig


class AttendanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'attendance'

    def ready(self):
        from django.db.models.signals import post_save, post_delete
        from .models import Attendance
        from .signals import _refresh_on_save, _refresh_on_delete
        post_save.connect(_refresh_on_save, sender=Attendance)
        post_delete.connect(_refresh_on_delete, sender=Attendance)
