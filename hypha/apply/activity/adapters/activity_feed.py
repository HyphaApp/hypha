import json

from django.db.models import Model as DjangoModel
from django.utils import timezone
from django.utils.translation import gettext as _

from hypha.apply.activity.models import ALL, TEAM
from hypha.apply.activity.options import MESSAGES

from .base import AdapterBase
from .utils import is_transition, reviewers_message


class ActivityAdapter(AdapterBase):
    adapter_type = "Activity Feed"
    always_send = True
    messages = {
        MESSAGES.TRANSITION: 'handle_transition',
        MESSAGES.BATCH_TRANSITION: 'handle_batch_transition',
        MESSAGES.NEW_SUBMISSION: _('Submitted {source.title} for {source.page.title}'),
        MESSAGES.EDIT_SUBMISSION: _('Edited'),
        MESSAGES.APPLICANT_EDIT: _('Edited'),
        MESSAGES.UPDATE_LEAD: _('Lead changed from {old_lead} to {source.lead}'),
        MESSAGES.BATCH_UPDATE_LEAD: _('Batch Lead changed to {new_lead}'),
        MESSAGES.DETERMINATION_OUTCOME: _('Sent a determination. Outcome: {determination.clean_outcome}'),
        MESSAGES.BATCH_DETERMINATION_OUTCOME: 'batch_determination',
        MESSAGES.INVITED_TO_PROPOSAL: _('Invited to submit a proposal'),
        MESSAGES.REVIEWERS_UPDATED: 'reviewers_updated',
        MESSAGES.BATCH_REVIEWERS_UPDATED: 'batch_reviewers_updated',
        MESSAGES.PARTNERS_UPDATED: 'partners_updated',
        MESSAGES.NEW_REVIEW: _('Submitted a review'),
        MESSAGES.OPENED_SEALED: _('Opened the submission while still sealed'),
        MESSAGES.SCREENING: 'handle_screening_statuses',
        MESSAGES.REVIEW_OPINION: _('{user} {opinion.opinion_display}s with {opinion.review.author}s review of {source}'),
        MESSAGES.CREATED_PROJECT: _('Created'),
        MESSAGES.PROJECT_TRANSITION: _('Progressed from {old_stage} to {source.status_display}'),
        MESSAGES.UPDATE_PROJECT_LEAD: _('Lead changed from {old_lead} to {source.lead}'),
        MESSAGES.SEND_FOR_APPROVAL: _('Requested approval'),
        MESSAGES.APPROVE_PROJECT: _('Approved'),
        MESSAGES.REQUEST_PROJECT_CHANGE: _('Requested changes for acceptance: "{comment}"'),
        MESSAGES.UPLOAD_CONTRACT: _('Uploaded a {contract.state} contract'),
        MESSAGES.APPROVE_CONTRACT: _('Approved contract'),
        MESSAGES.UPDATE_INVOICE_STATUS: 'handle_update_invoice_status',
        MESSAGES.CREATE_INVOICE: _('Invoice created'),
        MESSAGES.SUBMIT_REPORT: _('Submitted a report'),
        MESSAGES.SKIPPED_REPORT: 'handle_skipped_report',
        MESSAGES.REPORT_FREQUENCY_CHANGED: 'handle_report_frequency',
        MESSAGES.BATCH_DELETE_SUBMISSION: 'handle_batch_delete_submission',
    }

    def recipients(self, message_type, **kwargs):
        return [None]

    def extra_kwargs(self, message_type, source, sources, **kwargs):
        if message_type in [
            MESSAGES.OPENED_SEALED,
            MESSAGES.REVIEWERS_UPDATED,
            MESSAGES.SCREENING,
            MESSAGES.REVIEW_OPINION,
            MESSAGES.BATCH_REVIEWERS_UPDATED,
            MESSAGES.PARTNERS_UPDATED,
            MESSAGES.APPROVE_PROJECT,
            MESSAGES.REQUEST_PROJECT_CHANGE,
            MESSAGES.SEND_FOR_APPROVAL,
            MESSAGES.NEW_REVIEW,
        ]:
            return {'visibility': TEAM}

        source = source or sources[0]
        if is_transition(message_type) and not source.phase.permissions.can_view(
            source.user
        ):
            # User's shouldn't see status activity changes for stages that aren't visible to the them
            return {'visibility': TEAM}
        return {}

    def reviewers_updated(self, added=list(), removed=list(), **kwargs):
        message = [_('Reviewers updated.')]
        if added:
            message.append(_('Added:'))
            message.extend(reviewers_message(added))

        if removed:
            message.append(_('Removed:'))
            message.extend(reviewers_message(removed))

        return ' '.join(message)

    def batch_reviewers_updated(self, added, **kwargs):
        base = [_('Batch Reviewers Updated.')]
        base.extend(
            [
                _('{user} as {name}.').format(user=str(user), name=role.name)
                for role, user in added
                if user
            ]
        )
        return ' '.join(base)

    def batch_determination(self, sources, determinations, **kwargs):
        submission = sources[0]
        determination = determinations[submission.id]
        return self.messages[MESSAGES.DETERMINATION_OUTCOME].format(
            determination=determination,
        )

    def handle_batch_delete_submission(self, sources, **kwargs):
        submissions = sources
        submissions_text = ', '.join([submission.title for submission in submissions])
        return _('Successfully deleted submissions: {title}').format(
            title=submissions_text
        )

    def handle_transition(self, old_phase, source, **kwargs):
        submission = source
        base_message = _('Progressed from {old_display} to {new_display}')

        new_phase = submission.phase

        staff_message = base_message.format(
            old_display=old_phase.display_name,
            new_display=new_phase.display_name,
        )

        if new_phase.permissions.can_view(submission.user):
            # we need to provide a different message to the applicant
            if not old_phase.permissions.can_view(submission.user):
                old_phase = submission.workflow.previous_visible(
                    old_phase, submission.user
                )

            applicant_message = base_message.format(
                old_display=old_phase.public_name,
                new_display=new_phase.public_name,
            )

            return json.dumps(
                {
                    TEAM: staff_message,
                    ALL: applicant_message,
                }
            )

        return staff_message

    def handle_batch_transition(self, transitions, sources, **kwargs):
        submissions = sources
        kwargs.pop('source')
        for submission in submissions:
            old_phase = transitions[submission.id]
            return self.handle_transition(
                old_phase=old_phase, source=submission, **kwargs
            )

    def partners_updated(self, added, removed, **kwargs):
        message = [_('Partners updated.')]
        if added:
            message.append(_('Added:'))
            message.append(', '.join([str(user) for user in added]) + '.')

        if removed:
            message.append(_('Removed:'))
            message.append(', '.join([str(user) for user in removed]) + '.')

        return ' '.join(message)

    def handle_report_frequency(self, config, **kwargs):
        new_schedule = config.get_frequency_display()
        return _(
            'Updated reporting frequency. New schedule is: {new_schedule} starting on {schedule_start}'
        ).format(new_schedule=new_schedule, schedule_start=config.schedule_start)

    def handle_skipped_report(self, report, **kwargs):
        if report.skipped:
            return "Skipped a Report"
        else:
            return "Marked a Report as required"

    def handle_update_invoice_status(self, invoice, **kwargs):
        invoice_status_change = _('Updated Invoice status to: {status}.').format(
            status=invoice.status_display
        )
        return invoice_status_change

    def send_message(self, message, user, source, sources, **kwargs):
        from ..models import Activity

        visibility = kwargs.get('visibility', ALL)

        related = kwargs['related']
        if isinstance(related, dict):
            try:
                related = related[source.id]
            except KeyError:
                pass

        has_correct_fields = all(
            hasattr(related, attr) for attr in ['get_absolute_url']
        )
        isnt_source = source != related
        is_model = isinstance(related, DjangoModel)
        if has_correct_fields and isnt_source and is_model:
            related_object = related
        else:
            related_object = None

        Activity.actions.create(
            user=user,
            source=source,
            timestamp=timezone.now(),
            message=message,
            visibility=visibility,
            related_object=related_object,
        )

    def handle_screening_statuses(self, source, old_status, **kwargs):
        new_status = ', '.join([s.title for s in source.screening_statuses.all()])
        return _('Screening decision from {old_status} to {new_status}').format(
            old_status=old_status, new_status=new_status
        )
