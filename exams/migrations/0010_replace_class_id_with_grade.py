from django.db import migrations, models
import django.db.models.deletion


def populate_grade_from_class_id(apps, schema_editor):
    """
    Migrate existing class_id string values to the new grade FK.
    For each Exam row, look up a SchoolClass whose display_name matches
    the class_id string.  If no match is found or class_id is empty,
    assign the first SchoolClass as a default.
    """
    Exam = apps.get_model('exams', 'Exam')
    SchoolClass = apps.get_model('classes', 'SchoolClass')

    # Get a default SchoolClass (first one) for exams with empty/unmatched class_id
    default_class = SchoolClass.objects.first()
    default_class_pk = default_class.pk if default_class else None

    # Build a lookup: display_name -> pk
    class_lookup = {}
    for sc in SchoolClass.objects.all():
        key = f"{sc.name} - {sc.section}" if sc.section else sc.name
        class_lookup[key] = sc.pk
        # Also index by name alone for flexibility
        class_lookup[sc.name] = sc.pk

    for exam in Exam.objects.all():
        cid = exam.class_id
        if cid and cid in class_lookup:
            exam.grade_id = class_lookup[cid]
        else:
            # Assign default class when class_id is empty or unmatched
            exam.grade_id = default_class_pk
        exam.save(update_fields=['grade_id'])


def reverse_populate_class_id(apps, schema_editor):
    """Reverse: set class_id from grade FK (for rollback)."""
    Exam = apps.get_model('exams', 'Exam')
    SchoolClass = apps.get_model('classes', 'SchoolClass')

    for exam in Exam.objects.all():
        if exam.grade_id:
            sc = SchoolClass.objects.filter(pk=exam.grade_id).first()
            if sc:
                name = sc.name
                section = sc.section if hasattr(sc, 'section') else ''
                exam.class_id = f"{name} - {section}" if section else name
                exam.save(update_fields=['class_id'])


class Migration(migrations.Migration):

    dependencies = [
        ('exams', '0009_exam_total_grade'),
        ('classes', '0001_initial'),
    ]

    operations = [
        # Step 1: Add grade FK as nullable (so existing rows don't break)
        migrations.AddField(
            model_name='exam',
            name='grade',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='exams',
                to='classes.schoolclass',
                help_text='Grade/class this exam is for (e.g., Grade 5 - A)',
            ),
        ),

        # Step 2: Data migration – populate grade from class_id
        migrations.RunPython(
            populate_grade_from_class_id,
            reverse_populate_class_id,
        ),

        # Step 3: Make grade non-nullable (required field)
        migrations.AlterField(
            model_name='exam',
            name='grade',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='exams',
                to='classes.schoolclass',
                help_text='Grade/class this exam is for (e.g., Grade 5 - A)',
            ),
        ),

        # Step 4: Remove the old class_id field
        migrations.RemoveField(
            model_name='exam',
            name='class_id',
        ),
    ]