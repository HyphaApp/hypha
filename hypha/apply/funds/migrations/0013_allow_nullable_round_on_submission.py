# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2018-01-25 12:28
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("funds", "0012_create_lab_models"),
    ]

    operations = [
        migrations.AlterField(
            model_name="applicationsubmission",
            name="round",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="submissions",
                to="wagtailcore.Page",
            ),
        ),
    ]
