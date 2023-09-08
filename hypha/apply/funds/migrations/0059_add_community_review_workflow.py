# Generated by Django 2.0.10 on 2019-03-25 13:00

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("funds", "0058_add_group_toggle"),
    ]

    operations = [
        migrations.AlterField(
            model_name="applicationbase",
            name="workflow_name",
            field=models.CharField(
                choices=[
                    ("single", "Request"),
                    ("single_ext", "Request with external review"),
                    ("single_com", "Request with community review"),
                    ("double", "Concept & Proposal"),
                ],
                default="single",
                max_length=100,
                verbose_name="Workflow",
            ),
        ),
        migrations.AlterField(
            model_name="applicationsubmission",
            name="workflow_name",
            field=models.CharField(
                choices=[
                    ("single", "Request"),
                    ("single_ext", "Request with external review"),
                    ("single_com", "Request with community review"),
                    ("double", "Concept & Proposal"),
                ],
                default="single",
                max_length=100,
                verbose_name="Workflow",
            ),
        ),
        migrations.AlterField(
            model_name="labbase",
            name="workflow_name",
            field=models.CharField(
                choices=[
                    ("single", "Request"),
                    ("single_ext", "Request with external review"),
                    ("single_com", "Request with community review"),
                    ("double", "Concept & Proposal"),
                ],
                default="single",
                max_length=100,
                verbose_name="Workflow",
            ),
        ),
        migrations.AlterField(
            model_name="roundbase",
            name="workflow_name",
            field=models.CharField(
                choices=[
                    ("single", "Request"),
                    ("single_ext", "Request with external review"),
                    ("single_com", "Request with community review"),
                    ("double", "Concept & Proposal"),
                ],
                default="single",
                max_length=100,
                verbose_name="Workflow",
            ),
        ),
    ]
