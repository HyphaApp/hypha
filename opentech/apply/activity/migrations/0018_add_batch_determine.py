from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('activity', '0017_add_review_opinion'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='type',
            field=models.CharField(choices=[('UPDATE_LEAD', 'Update Lead'), ('EDIT', 'Edit'), ('APPLICANT_EDIT', 'Applicant Edit'), ('NEW_SUBMISSION', 'New Submission'), ('SCREENING', 'Screening'), ('TRANSITION', 'Transition'), ('BATCH_TRANSITION', 'Batch Transition'), ('DETERMINATION_OUTCOME', 'Determination Outcome'), ('BATCH_DETERMINATION_OUTCOME', 'Batch Determination Outcome'), ('INVITED_TO_PROPOSAL', 'Invited To Proposal'), ('REVIEWERS_UPDATED', 'Reviewers Updated'), ('BATCH_REVIEWERS_UPDATED', 'Batch Reviewers Updated'), ('READY_FOR_REVIEW', 'Ready For Review'), ('BATCH_READY_FOR_REVIEW', 'Batch Ready For Review'), ('NEW_REVIEW', 'New Review'), ('COMMENT', 'Comment'), ('PROPOSAL_SUBMITTED', 'Proposal Submitted'), ('OPENED_SEALED', 'Opened Sealed Submission'), ('REVIEW_OPINION', 'Review Opinion')], max_length=50),
        ),
    ]
