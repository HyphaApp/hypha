# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-12-15 13:15
from __future__ import unicode_literals

from django.db import migrations


def add_groups(apps, schema_editor):
    pass


def remove_groups(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0001_initial"),
        ("wagtailadmin", "0001_create_admin_access_permissions"),
        ("wagtailimages", "0002_initial_data"),
        ("wagtaildocs", "0002_initial_data"),
        ("contenttypes", "__latest__"),
    ]

    operations = [migrations.RunPython(add_groups, remove_groups)]
