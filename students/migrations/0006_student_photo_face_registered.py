from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0005_student_school_class'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='photo',
            field=models.ImageField(
                blank=True,
                help_text='Clear face photo used for attendance face recognition',
                null=True,
                upload_to='student_photos/',
            ),
        ),
        migrations.AddField(
            model_name='student',
            name='face_registered',
            field=models.BooleanField(
                default=False,
                help_text='True when a face encoding has been successfully registered in the face recognition service',
            ),
        ),
    ]
