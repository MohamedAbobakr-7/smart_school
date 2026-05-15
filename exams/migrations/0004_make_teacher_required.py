# Generated manually
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('exams', '0003_restructure_exam_system'),
    ]

    operations = [
        migrations.AlterField(
            model_name='exam',
            name='teacher',
            field=models.ForeignKey(
                help_text='Teacher who created this exam',
                on_delete=models.CASCADE,
                related_name='created_exams',
                to='teachers.teacher'
            ),
        ),
    ]

