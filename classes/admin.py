from django.contrib import admin
from .models import SchoolClass


@admin.register(SchoolClass)
class SchoolClassAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'name', 'section', 'created_at']
    list_filter = ['name', 'section']
    search_fields = ['name', 'section', 'description']
    ordering = ['name', 'section']
