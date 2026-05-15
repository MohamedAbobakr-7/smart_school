from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subjects', '0003_remove_subject_teacher_alter_subject_code_and_more'),
        ('students', '0003_remove_student_grade_student_class_level_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='class_id',
            field=models.CharField(blank=True, help_text='Class identifier (e.g., G10-A, CLASS-01)', max_length=50),
        ),
        migrations.AddField(
            model_name='student',
            name='subjects',
            field=models.ManyToManyField(
                blank=True,
                help_text='Subjects this student is enrolled in',
                related_name='enrolled_students',
                to='subjects.subject',
            ),
        ),
        migrations.AddIndex(
            model_name='student',
            index=models.Index(fields=['class_id'], name='students_class_i_a4a74e_idx'),
        ),
    ]
