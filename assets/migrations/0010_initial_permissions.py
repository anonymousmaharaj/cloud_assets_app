# Generated by Django 3.0.14 on 2021-10-11 21:45

import os

from django.contrib.auth import get_user_model
from django.db import migrations


def create_permissions(apps, schema_editor):
    model = apps.get_model('assets', 'Permissions')
    model.objects.create(title='Download', name='read_only').save()
    model.objects.create(title='Rename', name='rename_only').save()
    model.objects.create(title='Delete', name='delete_only').save()


class Migration(migrations.Migration):
    dependencies = [
        ('assets', '0009_delete_null_in_extention'),
    ]

    operations = [
        migrations.RunPython(create_permissions, reverse_code=migrations.RunPython.noop),
    ]
