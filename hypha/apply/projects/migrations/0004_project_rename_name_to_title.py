# Generated by Django 2.0.13 on 2019-07-11 03:20

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("application_projects", "0003_add_project_lead"),
    ]

    operations = [
        migrations.RenameField(
            model_name="project",
            old_name="name",
            new_name="title",
        ),
    ]
