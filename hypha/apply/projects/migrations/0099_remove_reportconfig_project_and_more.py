# Generated by Django 4.2.20 on 2025-03-26 07:02

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("application_projects", "0098_move_project_comments_to_application"),
        (
            "project_reports",
            "0001_initial",
        ),
    ]

    state_operations = [
        migrations.RemoveField(
            model_name="reportconfig",
            name="project",
        ),
        migrations.RemoveField(
            model_name="reportprivatefiles",
            name="report",
        ),
        migrations.RemoveField(
            model_name="reportversion",
            name="author",
        ),
        migrations.RemoveField(
            model_name="reportversion",
            name="report",
        ),
        migrations.DeleteModel(
            name="Report",
        ),
        migrations.DeleteModel(
            name="ReportConfig",
        ),
        migrations.DeleteModel(
            name="ReportPrivateFiles",
        ),
        migrations.DeleteModel(
            name="ReportVersion",
        ),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(state_operations=state_operations)
    ]
