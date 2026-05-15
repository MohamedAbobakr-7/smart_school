from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('subjects', '0003_remove_subject_teacher_alter_subject_code_and_more'),
        ('teachers', '0003_teacher_assigned_subjects_alter_teacher_department_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='TeacherSubjectClass',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('class_id', models.CharField(help_text='Class identifier (e.g., G10-A, CLASS-01)', max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='teacher_class_relations', to='subjects.subject')),
                ('teacher', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subject_class_relations', to='teachers.teacher')),
            ],
            options={
                'verbose_name': 'Teacher Subject Class',
                'verbose_name_plural': 'Teacher Subject Classes',
                'db_table': 'teacher_subject_classes',
                'ordering': ['teacher_id', 'subject_id', 'class_id'],
            },
        ),
        migrations.AddIndex(
            model_name='teachersubjectclass',
            index=models.Index(fields=['teacher'], name='teacher_sub_teacher_598c81_idx'),
        ),
        migrations.AddIndex(
            model_name='teachersubjectclass',
            index=models.Index(fields=['subject'], name='teacher_sub_subject_be3b5d_idx'),
        ),
        migrations.AddIndex(
            model_name='teachersubjectclass',
            index=models.Index(fields=['class_id'], name='teacher_sub_class_i_5166c8_idx'),
        ),
        migrations.AddConstraint(
            model_name='teachersubjectclass',
            constraint=models.UniqueConstraint(fields=('teacher', 'subject', 'class_id'), name='uniq_teacher_subject_class'),
        ),
    ]
