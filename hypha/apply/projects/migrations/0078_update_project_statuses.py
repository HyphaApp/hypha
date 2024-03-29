# Generated by Django 3.2.19 on 2023-07-19 11:54

from django.db import migrations, models


def update_project_statuses(apps, schema_editor):
    Project = apps.get_model("application_projects", "Project")

    for project in Project.objects.filter(status="waiting_for_approval"):
        project.status = "internal_approval"
        project.save(update_fields={"status"})

    for project in Project.objects.filter(status="in_progress"):
        project.status = "invoicing_and_reporting"
        project.save()


class Migration(migrations.Migration):
    dependencies = [
        ("application_projects", "0077_alter_invoice_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="project",
            name="status",
            field=models.TextField(
                choices=[
                    ("draft", "Draft"),
                    ("internal_approval", "Internal approval"),
                    ("contracting", "Contracting"),
                    ("invoicing_and_reporting", "Invoicing and reporting"),
                    ("closing", "Closing"),
                    ("complete", "Complete"),
                ],
                default="draft",
            ),
        ),
        migrations.RunPython(update_project_statuses),
    ]
