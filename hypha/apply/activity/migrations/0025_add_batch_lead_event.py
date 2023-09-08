# Generated by Django 2.0.13 on 2019-07-30 05:28

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("activity", "0024_add_review_edit_event"),
    ]

    operations = [
        migrations.AlterField(
            model_name="event",
            name="type",
            field=models.CharField(
                choices=[
                    ("UPDATE_LEAD", "Update Lead"),
                    ("BATCH_UPDATE_LEAD", "Batch Update Lead"),
                    ("EDIT", "Edit"),
                    ("APPLICANT_EDIT", "Applicant Edit"),
                    ("NEW_SUBMISSION", "New Submission"),
                    ("SCREENING", "Screening"),
                    ("TRANSITION", "Transition"),
                    ("BATCH_TRANSITION", "Batch Transition"),
                    ("DETERMINATION_OUTCOME", "Determination Outcome"),
                    ("BATCH_DETERMINATION_OUTCOME", "Batch Determination Outcome"),
                    ("INVITED_TO_PROPOSAL", "Invited To Proposal"),
                    ("REVIEWERS_UPDATED", "Reviewers Updated"),
                    ("BATCH_REVIEWERS_UPDATED", "Batch Reviewers Updated"),
                    ("PARTNERS_UPDATED", "Partners Updated"),
                    ("PARTNERS_UPDATED_PARTNER", "Partners Updated Partner"),
                    ("READY_FOR_REVIEW", "Ready For Review"),
                    ("BATCH_READY_FOR_REVIEW", "Batch Ready For Review"),
                    ("NEW_REVIEW", "New Review"),
                    ("COMMENT", "Comment"),
                    ("PROPOSAL_SUBMITTED", "Proposal Submitted"),
                    ("OPENED_SEALED", "Opened Sealed Submission"),
                    ("REVIEW_OPINION", "Review Opinion"),
                    ("DELETE_SUBMISSION", "Delete Submission"),
                    ("DELETE_REVIEW", "Delete Review"),
                    ("EDIT_REVIEW", "Edit Review"),
                ],
                max_length=50,
            ),
        ),
    ]
