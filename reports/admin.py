from django.contrib import admin

from .models import Report, WeeklyReport


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'report_type', 'student', 'generated_at')
    list_filter = ('report_type',)


@admin.register(WeeklyReport)
class WeeklyReportAdmin(admin.ModelAdmin):
    list_display = (
        'week_start',
        'week_end',
        'scope',
        'teacher',
        'status',
        'generated_at',
    )
    list_filter = ('scope', 'status')
    readonly_fields = ('dedupe_key', 'generated_at', 'created_at', 'updated_at')
