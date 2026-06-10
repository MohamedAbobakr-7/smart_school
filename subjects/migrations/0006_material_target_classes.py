# Generated migration for adding target_classes to Material

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subjects', '0005_material_description_ar_material_description_en_and_more'),
        ('classes', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='material',
            name='target_classes',
            field=models.ManyToManyField(
                help_text='Target classes for this educational material.',
                related_name='materials',
                to='classes.schoolclass',
            ),
        ),
    ]