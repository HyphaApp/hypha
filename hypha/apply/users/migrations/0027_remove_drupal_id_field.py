# Generated by Django 4.2.17 on 2025-01-14 08:41

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0026_delete_groupdesc"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="user",
            name="drupal_id",
        ),
    ]
