# Generated manually
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('exams', '0005_add_exam_date_class_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='exam',
            name='exam_type',
            field=models.CharField(choices=[('quiz', 'Quiz'), ('homework', 'Homework'), ('midterm', 'Midterm'), ('final', 'Final'), ('assignment', 'Assignment'), ('oral_exam', 'Oral Exam')], default='quiz', help_text='Type of assessment', max_length=20),
        ),
    ]
