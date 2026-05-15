from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('classes', '0001_initial'),
        ('students', '0004_student_class_id_and_subjects'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='school_class',
            field=models.ForeignKey(
                blank=True,
                help_text='Assigned class group for this student',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='students',
                to='classes.schoolclass',
            ),
        ),
    ]
