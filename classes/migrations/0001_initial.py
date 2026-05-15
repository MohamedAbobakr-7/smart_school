from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='SchoolClass',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Grade/class name (e.g., Grade 5, Year 10)', max_length=100)),
                ('section', models.CharField(blank=True, default='', help_text='Section label (e.g., A, B, C). Leave blank for no section.', max_length=10)),
                ('description', models.TextField(blank=True, default='', help_text='Optional description or notes about this class.')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Class',
                'verbose_name_plural': 'Classes',
                'db_table': 'school_classes',
                'ordering': ['name', 'section'],
                'indexes': [
                    models.Index(fields=['name'], name='school_clas_name_idx'),
                    models.Index(fields=['section'], name='school_clas_section_idx'),
                ],
            },
        ),
        migrations.AlterUniqueTogether(
            name='schoolclass',
            unique_together={('name', 'section')},
        ),
    ]
