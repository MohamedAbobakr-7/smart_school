from django.contrib import admin
from .models import SubjectEnrollment


class SubjectEnrollmentAdmin(admin.ModelAdmin):
    """
    SubjectEnrollment is synced automatically via signals with Student.subjects M2M.
    Hide it from the admin index so admins manage enrollments through the Student form instead.
    Direct URL access still works if needed.
    """
    def get_model_perms(self, request):
        return {}


admin.site.register(SubjectEnrollment, SubjectEnrollmentAdmin)
