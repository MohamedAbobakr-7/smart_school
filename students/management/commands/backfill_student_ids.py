"""
Management command: backfill_student_ids

Assigns auto-generated Student IDs to existing students that have a blank
or missing student_id.

Usage:
    python manage.py backfill_student_ids
    python manage.py backfill_student_ids --dry-run
"""

from django.core.management.base import BaseCommand
from students.utils import backfill_student_ids, students_missing_ids_queryset


class Command(BaseCommand):
    help = 'Auto-generate Student IDs for existing students that are missing one.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview how many students would be updated without saving.',
        )

    def handle(self, *args, **options):
        qs = students_missing_ids_queryset()
        count = qs.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS('All students already have IDs. Nothing to do.'))
            return

        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING(f'[DRY RUN] {count} students would receive auto-generated IDs.')
            )
            for s in qs:
                from students.utils import generate_student_id
                preview_id = generate_student_id(school_class=s.school_class)
                self.stdout.write(f'  Student pk={s.pk} → {preview_id}')
            return

        updated = backfill_student_ids()
        self.stdout.write(
            self.style.SUCCESS(f'Successfully assigned IDs to {updated} student(s).')
        )
