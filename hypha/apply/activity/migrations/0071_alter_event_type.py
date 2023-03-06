# Generated by Django 3.2.18 on 2023-03-06 04:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('activity', '0070_alter_event_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='type',
            field=models.CharField(choices=[('UPDATE_LEAD', 'updated lead'), ('BATCH_UPDATE_LEAD', 'batch updated lead'), ('EDIT_SUBMISSION', 'edited submission'), ('APPLICANT_EDIT', 'edited applicant'), ('NEW_SUBMISSION', 'submitted new submission'), ('DRAFT_SUBMISSION', 'submitted new draft submission'), ('SCREENING', 'screened'), ('TRANSITION', 'transitioned'), ('BATCH_TRANSITION', 'batch transitioned'), ('DETERMINATION_OUTCOME', 'sent determination outcome'), ('BATCH_DETERMINATION_OUTCOME', 'sent batch determination outcome'), ('INVITED_TO_PROPOSAL', 'invited to proposal'), ('REVIEWERS_UPDATED', 'updated reviewers'), ('BATCH_REVIEWERS_UPDATED', 'batch updated reviewers'), ('PARTNERS_UPDATED', 'updated partners'), ('PARTNERS_UPDATED_PARTNER', 'partners updated partner'), ('READY_FOR_REVIEW', 'marked ready for review'), ('BATCH_READY_FOR_REVIEW', 'marked batch ready for review'), ('NEW_REVIEW', 'added new review'), ('COMMENT', 'added comment'), ('PROPOSAL_SUBMITTED', 'submitted proposal'), ('OPENED_SEALED', 'opened sealed submission'), ('REVIEW_OPINION', 'reviewed opinion'), ('DELETE_SUBMISSION', 'deleted submission'), ('DELETE_REVIEW', 'deleted review'), ('CREATED_PROJECT', 'created project'), ('UPDATED_VENDOR', 'updated contracting information'), ('UPDATE_PROJECT_LEAD', 'updated project lead'), ('EDIT_REVIEW', 'edited review'), ('SEND_FOR_APPROVAL', 'sent for approval'), ('APPROVE_PROJECT', 'approved project'), ('APPROVE_PAF', 'approved paf'), ('PROJECT_TRANSITION', 'transitioned project'), ('REQUEST_PROJECT_CHANGE', 'requested project change'), ('UPLOAD_DOCUMENT', 'uploaded document to project'), ('REMOVE_DOCUMENT', 'removed document from project'), ('UPLOAD_CONTRACT', 'uploaded contract to project'), ('APPROVE_CONTRACT', 'approved contract'), ('CREATE_INVOICE', 'created invoice for project'), ('UPDATE_INVOICE_STATUS', 'updated invoice status'), ('DELETE_INVOICE', 'deleted invoice'), ('SENT_TO_COMPLIANCE', 'sent project to compliance'), ('UPDATE_INVOICE', 'updated invoice'), ('SUBMIT_REPORT', 'submitted report'), ('SKIPPED_REPORT', 'skipped report'), ('REPORT_FREQUENCY_CHANGED', 'changed report frequency'), ('DISABLED_REPORTING', 'disabled reporting'), ('REPORT_NOTIFY', 'notified report'), ('CREATE_REMINDER', 'created reminder'), ('DELETE_REMINDER', 'deleted reminder'), ('REVIEW_REMINDER', 'reminder to review'), ('BATCH_DELETE_SUBMISSION', 'batch deleted submissions'), ('BATCH_ARCHIVE_SUBMISSION', 'batch archive submissions'), ('STAFF_ACCOUNT_CREATED', 'created new account'), ('STAFF_ACCOUNT_EDITED', 'edited account'), ('ARCHIVE_SUBMISSION', 'archived submission'), ('UNARCHIVE_SUBMISSION', 'unarchived submission')], max_length=50, verbose_name='verb'),
        ),
    ]
