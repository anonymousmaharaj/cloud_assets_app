# Generated by Django 3.0.14 on 2021-09-09 14:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0003_edit_max_length_in_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='file',
            name='relative_key',
            field=models.CharField(default=1, max_length=255),
            preserve_default=False,
        ),
    ]
