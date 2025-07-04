# Generated by Django 2.0.2 on 2018-06-11 16:14

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("funds", "0032_make_reviewers_optional_in_all_instances"),
    ]

    operations = [
        migrations.AlterField(
            model_name="applicationsubmission",
            name="status",
            field=models.CharField(
                default="in_discussion",
                max_length=50,
            ),
        ),
        migrations.AlterField(
            model_name="applicationsubmission",
            name="workflow_name",
            field=models.CharField(
                choices=[("single", "Request"), ("double", "Concept & Proposal")],
                default="single",
                max_length=100,
                verbose_name="Workflow",
            ),
        ),
        migrations.AlterField(
            model_name="fundtype",
            name="workflow_name",
            field=models.CharField(
                choices=[("single", "Request"), ("double", "Concept & Proposal")],
                default="single",
                max_length=100,
                verbose_name="Workflow",
            ),
        ),
        migrations.AlterField(
            model_name="labtype",
            name="workflow_name",
            field=models.CharField(
                choices=[("single", "Request"), ("double", "Concept & Proposal")],
                default="single",
                max_length=100,
                verbose_name="Workflow",
            ),
        ),
        migrations.AlterField(
            model_name="round",
            name="workflow_name",
            field=models.CharField(
                choices=[("single", "Request"), ("double", "Concept & Proposal")],
                default="single",
                max_length=100,
                verbose_name="Workflow",
            ),
        ),
    ]
