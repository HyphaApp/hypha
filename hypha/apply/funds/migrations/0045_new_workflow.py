# Generated by Django 2.0.8 on 2018-10-24 12:13

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("funds", "0044_add_named_blocks"),
    ]

    operations = [
        migrations.AlterField(
            model_name="applicationbase",
            name="workflow_name",
            field=models.CharField(
                choices=[
                    ("single", "Request"),
                    ("single_ext", "Request with external review"),
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
                    ("double", "Concept & Proposal"),
                ],
                default="single",
                max_length=100,
                verbose_name="Workflow",
            ),
        ),
    ]
