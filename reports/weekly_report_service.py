"""
Create and refresh WeeklyReport rows from analytics snapshots.
"""
from __future__ import annotations

from datetime import date, timedelta
from io import BytesIO

from django.core.files.base import ContentFile
from django.utils import timezone

from teachers.models import Teacher

from .models import WeeklyReport
from .weekly_analytics import build_weekly_snapshot, compare_to_prior_week
from .pdf_weekly import render_weekly_report_pdf


def week_bounds_iso(iso_year: int, iso_week: int) -> tuple[date, date]:
    """Monday–Sunday inclusive for the given ISO week."""
    monday = date.fromisocalendar(iso_year, iso_week, 1)
    sunday = monday + timedelta(days=6)
    return monday, sunday


def previous_completed_iso_week(today: date | None = None) -> tuple[date, date]:
    """Last fully completed ISO week (not the week containing `today`)."""
    d = today or timezone.now().date()
    this_monday = d - timedelta(days=d.weekday())
    last_sunday = this_monday - timedelta(days=1)
    last_monday = last_sunday - timedelta(days=6)
    return last_monday, last_sunday


def upsert_weekly_report(
    week_start: date,
    week_end: date,
    scope: str,
    teacher: Teacher | None = None,
    write_pdf: bool = True,
) -> WeeklyReport:
    """
    Build analytics, optionally render PDF, and save a READY WeeklyReport.
    """
    if scope == WeeklyReport.Scope.SCHOOL:
        teacher = None

    report, _created = WeeklyReport.objects.get_or_create(
        week_start=week_start,
        scope=scope,
        teacher=teacher,
        defaults={
            "week_end": week_end,
            "status": WeeklyReport.Status.PENDING,
        },
    )
    report.week_end = week_end

    try:
        snapshot = build_weekly_snapshot(week_start, week_end, teacher=teacher)
        comparison = compare_to_prior_week(week_start, week_end, teacher=teacher)
        report.attendance_stats = snapshot["attendance_stats"]
        report.academic_stats = snapshot["academic_stats"]
        report.exam_stats = snapshot["exam_stats"]
        report.charts_payload = snapshot["charts_payload"]
        report.insights = snapshot["insights"]
        report.comparison_prior_week = comparison
        report.error_message = ""
        report.status = WeeklyReport.Status.READY
        report.generated_at = timezone.now()
        report.save()

        if write_pdf:
            buf = BytesIO()
            render_weekly_report_pdf(report, buf)
            buf.seek(0)
            fname = f"weekly_{report.dedupe_key}.pdf"
            if report.pdf_file:
                report.pdf_file.delete(save=False)
            report.pdf_file.save(fname, ContentFile(buf.read()), save=True)
    except Exception as exc:
        report.status = WeeklyReport.Status.FAILED
        report.error_message = str(exc)[:2000]
        report.generated_at = timezone.now()
        report.save()

    return report


def generate_school_and_teacher_reports(
    week_start: date,
    week_end: date,
    write_pdf: bool = True,
) -> list[WeeklyReport]:
    """School-wide report plus one TEACHER report per Teacher row."""
    out: list[WeeklyReport] = []
    out.append(
        upsert_weekly_report(
            week_start,
            week_end,
            WeeklyReport.Scope.SCHOOL,
            teacher=None,
            write_pdf=write_pdf,
        )
    )
    for t in Teacher.objects.all().iterator():
        out.append(
            upsert_weekly_report(
                week_start,
                week_end,
                WeeklyReport.Scope.TEACHER,
                teacher=t,
                write_pdf=write_pdf,
            )
        )
    return out
