# Generated migration: replace field-level unique with filtered unique constraint
#
# SQL Server UNIQUE constraints only allow ONE NULL value, which breaks
# the "defer student ID" workflow where multiple students can have NULL
# student_id until the admin batch-generates IDs.
#
# This migration:
#   1. Removes unique=True from student_id CharField
#   2. Adds a filtered UniqueConstraint that only enforces uniqueness
#      for non-null student_id values (SQL Server filtered index)
#      Empty strings are also excluded because the serializer normalizes
#      them to NULL before saving.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0007_alter_student_student_id'),
    ]

    operations = [
        # Step 1: Remove the field-level unique constraint
        migrations.AlterField(
            model_name='student',
            name='student_id',
            field=models.CharField(
                blank=True,
                default=None,
                help_text='Unique identifier for the student. Auto-generated if left blank.',
                max_length=50,
                null=True,
                # unique=True removed — enforced via filtered constraint below
            ),
        ),
        # Step 2: Add filtered unique constraint (excludes NULL values)
        # Empty strings are normalized to NULL by the serializer, so we only
        # need to filter out NULLs. This creates a SQL Server filtered index:
        #   CREATE UNIQUE INDEX ... WHERE student_id IS NOT NULL
        migrations.AddConstraint(
            model_name='student',
            constraint=models.UniqueConstraint(
                condition=models.Q(student_id__isnull=False),
                fields=['student_id'],
                name='student_id_unique_nonnull',
            ),
        ),
    ]