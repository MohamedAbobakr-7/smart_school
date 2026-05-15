from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('classes', '0001_initial'),
        ('teachers', '0004_teachersubjectclass'),
    ]

    operations = [
        migrations.AddField(
            model_name='teacher',
            name='assigned_classes',
            field=models.ManyToManyField(
                blank=True,
                help_text='Classes assigned to this teacher',
                related_name='teachers',
                to='classes.schoolclass',
            ),
        ),
    ]
