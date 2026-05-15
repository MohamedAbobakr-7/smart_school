"""
Automated weekly report generation. Schedule with Task Scheduler / cron, e.g. Monday 06:00:

    python manage.py generate_weekly_reports

Optional: ISO week/year or explicit dates.
"""
from datetime import date

from django.core.management.base import BaseCommand

from reports.weekly_report_service import (
    generate_school_and_teacher_reports,
    previous_completed_iso_week,
    week_bounds_iso,
)


class Command(BaseCommand):
    help = "Generate school-wide and per-teacher WeeklyReport rows for a completed week."

    def add_arguments(self, parser):
        parser.add_argument(
            "--iso-year",
            type=int,
            default=None,
            help="ISO year (e.g. 2026). Use with --iso-week.",
        )
        parser.add_argument(
            "--iso-week",
            type=int,
            default=None,
            help="ISO week number 1–53.",
        )
        parser.add_argument(
            "--week-start",
            type=str,
            default=None,
            help="Week start date YYYY-MM-DD (inclusive). Use with --week-end.",
        )
        parser.add_argument(
            "--week-end",
            type=str,
            default=None,
            help="Week end date YYYY-MM-DD (inclusive).",
        )
        parser.add_argument(
            "--no-pdf",
            action="store_true",
            help="Skip PDF file generation (faster, JSON only).",
        )
        parser.add_argument(
            "--school-only",
            action="store_true",
            help="Only generate the school-wide report.",
        )

    def handle(self, *args, **options):
        iso_year = options["iso_year"]
        iso_week = options["iso_week"]
        ws = options["week_start"]
        we = options["week_end"]
        write_pdf = not options["no_pdf"]
        school_only = options["school_only"]

        if (iso_year is None) ^ (iso_week is None):
            self.stderr.write("Provide both --iso-year and --iso-week, or neither.")
            return

        if ws and we:
            week_start = date.fromisoformat(ws)
            week_end = date.fromisoformat(we)
        elif iso_year is not None:
            week_start, week_end = week_bounds_iso(iso_year, iso_week)
        else:
            week_start, week_end = previous_completed_iso_week()

        self.stdout.write(f"Generating reports for {week_start} .. {week_end}")

        if school_only:
            from reports.weekly_report_service import upsert_weekly_report
            from reports.models import WeeklyReport

            upsert_weekly_report(
                week_start,
                week_end,
                WeeklyReport.Scope.SCHOOL,
                teacher=None,
                write_pdf=write_pdf,
            )
            self.stdout.write(self.style.SUCCESS("School weekly report ready."))
            return

        reports = generate_school_and_teacher_reports(
            week_start, week_end, write_pdf=write_pdf
        )
        self.stdout.write(self.style.SUCCESS(f"Generated {len(reports)} weekly report(s)."))
