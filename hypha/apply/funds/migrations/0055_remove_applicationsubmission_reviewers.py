# Generated by Django 2.0.10 on 2019-02-07 16:17

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("funds", "0054_move_reviewer_data"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="applicationsubmission",
            name="reviewers",
        ),
    ]
