# Generated by Django 2.0.13 on 2019-08-26 07:41

from django.db import migrations, models

from hypha.apply.activity.models import COMMENT, APPLICANT, TEAM, ALL


def update_visibility_options(apps, schema_editor):
    Activity = apps.get_model("activity", "Activity")
    for comment in Activity.objects.filter(type=COMMENT):
        updated = False
        if comment.visibility == "private":
            comment.visibility = APPLICANT
            updated = True
        elif comment.visibility == "internal":
            comment.visibility = TEAM
            updated = True
        elif comment.visibility == "public":
            comment.visibility = ALL
            updated = True

        if updated:
            comment.save()


class Migration(migrations.Migration):
    dependencies = [
        ("activity", "0025_add_batch_lead_event"),
    ]

    operations = [
        migrations.AlterField(
            model_name="activity",
            name="visibility",
            field=models.CharField(
                choices=[
                    ("applicant", "Applicant(s)"),
                    ("team", "Team"),
                    ("reviewers", "Reviewers"),
                    ("partners", "Partners"),
                    ("all", "All"),
                ],
                default="applicant",
                max_length=30,
            ),
        ),
        migrations.RunPython(update_visibility_options, migrations.RunPython.noop),
    ]
