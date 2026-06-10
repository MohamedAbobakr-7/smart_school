from django.db import migrations, models


def migrate_grade_fk_to_char(apps, schema_editor):
    """
    Convert existing grade FK values (SchoolClass) to grade-level strings.
    For each Exam, look at the linked SchoolClass.name and extract the
    grade level number (e.g., "Grade 5" -> "5", "KG" -> "KG").
    """
    Exam = apps.get_model('exams', 'Exam')
    SchoolClass = apps.get_model('classes', 'SchoolClass')

    # Mapping from common SchoolClass.name patterns to grade choice values
    grade_map = {
        'kindergarten': 'KG',
        'kg': 'KG',
        'grade 1': '1',
        'grade 2': '2',
        'grade 3': '3',
        'grade 4': '4',
        'grade 5': '5',
        'grade 6': '6',
        'grade 7': '7',
        'grade 8': '8',
        'grade 9': '9',
        'grade 10': '10',
        'grade 11': '11',
        'grade 12': '12',
        'year 1': '1',
        'year 2': '2',
        'year 3': '3',
        'year 4': '4',
        'year 5': '5',
        'year 6': '6',
        'year 7': '7',
        'year 8': '8',
        'year 9': '9',
        'year 10': '10',
        'year 11': '11',
        'year 12': '12',
        '1': '1',
        '2': '2',
        '3': '3',
        '4': '4',
        '5': '5',
        '6': '6',
        '7': '7',
        '8': '8',
        '9': '9',
        '10': '10',
        '11': '11',
        '12': '12',
    }

    for exam in Exam.objects.all():
        if exam.grade_id:
            sc = SchoolClass.objects.filter(pk=exam.grade_id).first()
            if sc:
                name_lower = sc.name.lower().strip()
                # Try direct mapping
                grade_value = grade_map.get(name_lower, None)
                if grade_value is None:
                    # Try extracting number from name like "Grade 5 - A" or "Grade 5"
                    import re
                    match = re.search(r'(\d+)', sc.name)
                    if match:
                        grade_value = match.group(1)
                    elif 'kg' in name_lower or 'kindergarten' in name_lower:
                        grade_value = 'KG'
                    else:
                        # Default to '1' if no match found
                        grade_value = '1'
                exam.grade_new = grade_value
                exam.save(update_fields=['grade_new'])
        else:
            # No grade FK set, default to '1'
            exam.grade_new = '1'
            exam.save(update_fields=['grade_new'])


def reverse_migrate_grade_char_to_fk(apps, schema_editor):
    """
    Reverse: convert grade char values back to SchoolClass FK.
    Find a SchoolClass whose name contains the grade level.
    """
    Exam = apps.get_model('exams', 'Exam')
    SchoolClass = apps.get_model('classes', 'SchoolClass')

    for exam in Exam.objects.all():
        grade_val = exam.grade
        if grade_val == 'KG':
            # Find a KG class
            sc = SchoolClass.objects.filter(name__icontains='kg').first()
        else:
            # Find a class matching the grade number
            sc = SchoolClass.objects.filter(name__icontains=f'Grade {grade_val}').first()
            if not sc:
                sc = SchoolClass.objects.filter(name__icontains=grade_val).first()

        if sc:
            exam.grade_id = sc.pk
        else:
            # Fallback to first SchoolClass
            first_sc = SchoolClass.objects.first()
            exam.grade_id = first_sc.pk if first_sc else None
        exam.save(update_fields=['grade_id'])


class Migration(migrations.Migration):

    dependencies = [
        ('exams', '0010_replace_class_id_with_grade'),
        ('classes', '0001_initial'),
    ]

    operations = [
        # Step 1: Add new grade CharField as nullable temporarily
        migrations.AddField(
            model_name='exam',
            name='grade_new',
            field=models.CharField(
                blank=True,
                max_length=10,
                null=True,
                help_text='Grade level this exam is for (e.g., 1, 2, 3... 12, KG)',
            ),
        ),

        # Step 2: Data migration – populate grade_new from grade FK
        migrations.RunPython(
            migrate_grade_fk_to_char,
            reverse_migrate_grade_char_to_fk,
        ),

        # Step 3: Remove the old grade FK field
        migrations.RemoveField(
            model_name='exam',
            name='grade',
        ),

        # Step 4: Rename grade_new -> grade and make it required
        migrations.RenameField(
            model_name='exam',
            old_name='grade_new',
            new_name='grade',
        ),

        # Step 5: Make grade non-nullable (required)
        migrations.AlterField(
            model_name='exam',
            name='grade',
            field=models.CharField(
                max_length=10,
                help_text='Grade level this exam is for (e.g., 1, 2, 3... 12, KG)',
            ),
        ),
    ]