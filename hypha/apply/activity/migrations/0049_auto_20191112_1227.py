# Generated by Django 2.1.11 on 2019-11-12 12:27

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("activity", "0048_add_project_transition"),
    ]

    operations = [
        migrations.AlterField(
            model_name="activity",
            name="source_object_id",
            field=models.PositiveIntegerField(blank=True, db_index=True, null=True),
        ),
    ]
