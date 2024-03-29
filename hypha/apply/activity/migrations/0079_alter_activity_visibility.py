# Generated by Django 4.2.9 on 2024-02-01 19:30

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("activity", "0078_activityattachment"),
    ]

    operations = [
        migrations.AlterField(
            model_name="activity",
            name="visibility",
            field=models.CharField(
                choices=[
                    ("applicant", "Applicants"),
                    ("team", "Staff only"),
                    ("reviewers", "Reviewers"),
                    ("partners", "Partners"),
                    ("all", "All"),
                    ("applicant partners", "Applicants & Partners"),
                ],
                default="applicant",
                max_length=30,
            ),
        ),
    ]
