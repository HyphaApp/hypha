# Generated by Django 3.2.18 on 2023-03-23 07:29

import django.core.files.storage
from django.db import migrations, models
import django.db.models.deletion
import hypha.apply.projects.models.project


class Migration(migrations.Migration):
    dependencies = [
        ("application_projects", "0068_rename_section_text_field"),
    ]

    operations = [
        migrations.CreateModel(
            name="ContractDocumentCategory",
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
                ("name", models.CharField(max_length=254)),
                ("recommended_minimum", models.PositiveIntegerField()),
            ],
            options={
                "verbose_name_plural": "Contract Document Categories",
                "ordering": ("name",),
            },
        ),
        migrations.AlterModelOptions(
            name="documentcategory",
            options={
                "ordering": ("name",),
                "verbose_name_plural": "Project Document Categories",
            },
        ),
        migrations.RemoveField(
            model_name="contract",
            name="is_signed",
        ),
        migrations.AddField(
            model_name="contract",
            name="signed_by_applicant",
            field=models.BooleanField(default=False, verbose_name="Counter Signed?"),
        ),
        migrations.AddField(
            model_name="project",
            name="submitted_contract_documents",
            field=models.BooleanField(
                default=False, verbose_name="Submit Contracting Documents"
            ),
        ),
        migrations.CreateModel(
            name="ContractPacketFile",
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
                        storage=django.core.files.storage.FileSystemStorage(),
                        upload_to=hypha.apply.projects.models.project.contract_document_path,
                    ),
                ),
                ("created_at", models.DateField(auto_now_add=True, null=True)),
                (
                    "category",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="contract_packet_files",
                        to="application_projects.contractdocumentcategory",
                    ),
                ),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="contract_packet_files",
                        to="application_projects.project",
                    ),
                ),
            ],
        ),
    ]
