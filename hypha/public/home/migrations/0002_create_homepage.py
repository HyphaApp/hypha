# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def create_homepage(apps, schema_editor):
    """Do nothing. Code removed as the public home page is no longer part of the hypha."""
    return


class Migration(migrations.Migration):
    run_before = [
        ("wagtailcore", "0053_locale_model"),  # added for Wagtail 2.11 compatibility
    ]

    dependencies = [
        ("home", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_homepage),
    ]
