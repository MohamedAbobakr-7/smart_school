"""
Management command: detect_at_risk

Scans all students for at-risk criteria and sends notifications:
  - Absences >= 3 within recent 30-day period
  OR
  - Average grade percentage < 50%

When detected, notifications are sent to:
  - Parent
  - Teacher(s) assigned to the student's class
  - Admin(s)

Usage:
    python manage.py detect_at_risk

Schedule this command via cron or Windows Task Scheduler to run daily:
    # Linux/Mac cron (daily at 8am)
    0 8 * * * /path/to/venv/bin/python /path/to/manage.py detect_at_risk

    # Windows Task Scheduler: run daily, action:
    python manage.py detect_at_risk
"""
from __future__ import annotations

from django.core.management.base import BaseCommand

from notifications.services import run_at_risk_detection


class Command(BaseCommand):
    help = "Detect at-risk students and send notifications to parents, teachers, and admins."

    def handle(self, *args, **options):
        self.stdout.write("Scanning students for at-risk criteria...")

        count = run_at_risk_detection()

        if count == 0:
            self.stdout.write(
                self.style.SUCCESS("No at-risk students detected.")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Done. {count} at-risk student(s) detected and notified."
                )
            )