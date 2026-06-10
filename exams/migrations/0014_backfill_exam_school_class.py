"""Backfill school_class FK from existing grade char values.

For each Exam that has a grade value (e.g. '5', 'KG') but no school_class,
find a matching SchoolClass and link it.
"""

from django.db import migrations


def backfill_school_class(apps, schema_editor):
    Exam = apps.get_model('exams', 'Exam')
    SchoolClass = apps.get_model('classes', 'SchoolClass')

    # Build a lookup: map grade-level strings to SchoolClass PKs
    # e.g. '5' -> first SchoolClass whose name contains "Grade 5" or "G5"
    #      'KG' -> first SchoolClass whose name contains "KG" or "Kindergarten"
    all_classes = SchoolClass.objects.all()

    grade_to_class = {}
    for sc in all_classes:
        name_lower = sc.name.lower()
        # Try to extract grade level from class name
        import re
        # "Grade N" or "G N" patterns
        m = re.search(r'\b(?:grade|g)\s*(\d{1,2})\b', name_lower)
        if m:
            grade_val = str(int(m.group(1)))
            if grade_val not in grade_to_class:
                grade_to_class[grade_val] = sc
        # "Year N" patterns
        m = re.search(r'\byear\s*(\d{1,2})\b', name_lower)
        if m:
            grade_val = str(int(m.group(1)))
            if grade_val not in grade_to_class:
                grade_to_class[grade_val] = sc
        # KG / Kindergarten
        if re.search(r'\bkg\b|\bkindergarten\b', name_lower):
            if 'KG' not in grade_to_class:
                grade_to_class['KG'] = sc

    # Backfill exams
    for exam in Exam.objects.filter(school_class__isnull=True).exclude(grade=''):
        matched_class = grade_to_class.get(exam.grade)
        if matched_class:
            exam.school_class = matched_class
            exam.save(update_fields=['school_class'])


def reverse_backfill(apps, schema_editor):
    """Reverse: clear school_class for all exams."""
    Exam = apps.get_model('exams', 'Exam')
    Exam.objects.all().update(school_class=None)


class Migration(migrations.Migration):

    dependencies = [
        ('exams', '0013_add_exam_school_class'),
        ('classes', '0003_alter_schoolclass_unique_together_and_more'),
    ]

    operations = [
        migrations.RunPython(
            backfill_school_class,
            reverse_backfill,
        ),
    ]