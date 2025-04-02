# Generated by Django 2.0.13 on 2019-08-07 15:50

from django.db import migrations, models
import django.db.models.deletion
import hypha.apply.projects.models


class Migration(migrations.Migration):
    dependencies = [
        ("application_projects", "0010_add_related_names_to_approval_fks"),
    ]

    operations = [
        migrations.CreateModel(
            name="PacketFile",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.TextField()),
                (
                    "document",
                    models.FileField(
                        upload_to=hypha.apply.projects.models.projects.document_path
                    ),
                ),
                (
                    "category",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="packet_files",
                        to="application_projects.DocumentCategory",
                    ),
                ),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="packet_files",
                        to="application_projects.Project",
                    ),
                ),
            ],
        ),
    ]
