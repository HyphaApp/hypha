# Generated by Django 2.0.10 on 2019-02-07 15:54

from django.db import migrations


def move_reviewer_data(apps, schema_editor):
    # We need to move data to the new `reviewers_new` field which will be renamed to `reviewers` in the next migration
    # This data migration is necessary because you cannot add a through model to an existing M2M field
    ApplicationSubmission = apps.get_model("funds", "ApplicationSubmission")
    AssignedReviewers = apps.get_model("funds", "AssignedReviewers")
    for submission in ApplicationSubmission.objects.all():
        AssignedReviewers.objects.bulk_create(
            AssignedReviewers(
                submission=submission,
                reviewer=reviewer,
                role=None,
            )
            for reviewer in submission.reviewers.all()
        )


class Migration(migrations.Migration):
    dependencies = [
        ("funds", "0053_assigned_reviewers_pre"),
    ]

    operations = [
        migrations.RunPython(
            move_reviewer_data, reverse_code=migrations.RunPython.noop
        ),
    ]
