import json
import logging
from collections import defaultdict

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db import models
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import gettext as _

from .models import ALL, TEAM
from .options import MESSAGES
from .tasks import send_mail

logger = logging.getLogger(__name__)
User = get_user_model()


def link_to(target, request):
    if target and hasattr(target, 'get_absolute_url'):
        return request.scheme + '://' + request.get_host() + target.get_absolute_url()


def group_reviewers(reviewers):
    groups = defaultdict(list)
    for reviewer in reviewers:
        groups[reviewer.role].append(reviewer.reviewer)
    return groups


def reviewers_message(reviewers):
    messages = []
    for role, reviewers in group_reviewers(reviewers).items():
        message = ', '.join(str(reviewer) for reviewer in reviewers)
        if role:
            message += _(' as {role}').format(role=str(role))
        message += '.'
        messages.append(message)
    return messages


neat_related = {
    MESSAGES.DETERMINATION_OUTCOME: 'determination',
    MESSAGES.BATCH_DETERMINATION_OUTCOME: 'determinations',
    MESSAGES.UPDATE_LEAD: 'old_lead',
    MESSAGES.NEW_REVIEW: 'review',
    MESSAGES.TRANSITION: 'old_phase',
    MESSAGES.BATCH_TRANSITION: 'transitions',
    MESSAGES.APPLICANT_EDIT: 'revision',
    MESSAGES.EDIT: 'revision',
    MESSAGES.COMMENT: 'comment',
    MESSAGES.SCREENING: 'old_status',
    MESSAGES.REVIEW_OPINION: 'opinion',
    MESSAGES.DELETE_REVIEW: 'review',
    MESSAGES.EDIT_REVIEW: 'review',
    MESSAGES.CREATED_PROJECT: 'submission',
    MESSAGES.PROJECT_TRANSITION: 'old_stage',
    MESSAGES.UPDATE_PROJECT_LEAD: 'old_lead',
    MESSAGES.APPROVE_CONTRACT: 'contract',
    MESSAGES.UPLOAD_CONTRACT: 'contract',
    MESSAGES.CREATE_INVOICE: 'create_invoice',
    MESSAGES.UPDATE_INVOICE_STATUS: 'invoice',
    MESSAGES.DELETE_INVOICE: 'invoice',
    MESSAGES.UPDATE_INVOICE: 'invoice',
    MESSAGES.SUBMIT_REPORT: 'report',
    MESSAGES.SKIPPED_REPORT: 'report',
    MESSAGES.REPORT_FREQUENCY_CHANGED: 'config',
    MESSAGES.REPORT_NOTIFY: 'report',
    MESSAGES.CREATE_REMINDER: 'reminder',
    MESSAGES.DELETE_REMINDER: 'reminder',
    MESSAGES.REVIEW_REMINDER: 'reminder',
}


def is_transition(message_type):
    return message_type in [MESSAGES.TRANSITION, MESSAGES.BATCH_TRANSITION]


def is_ready_for_review(message_type):
    return message_type in [MESSAGES.READY_FOR_REVIEW, MESSAGES.BATCH_READY_FOR_REVIEW]


def is_reviewer_update(message_type):
    return message_type in [MESSAGES.REVIEWERS_UPDATED, MESSAGES.BATCH_REVIEWERS_UPDATED]


class AdapterBase:
    messages = {}
    always_send = False

    def message(self, message_type, **kwargs):
        try:
            message = self.messages[message_type]
        except KeyError:
            # We don't know how to handle that message type
            return

        try:
            # see if its a method on the adapter
            method = getattr(self, message)
        except AttributeError:
            return self.render_message(message, **kwargs)
        else:
            # Delegate all responsibility to the custom method
            return method(**kwargs)

    def render_message(self, message, **kwargs):
        return message.format(**kwargs)

    def extra_kwargs(self, message_type, **kwargs):
        return {}

    def get_neat_related(self, message_type, related):
        # We translate the related kwarg into something we can understand
        try:
            neat_name = neat_related[message_type]
        except KeyError:
            # Message type doesn't expect a related object
            if related:
                raise ValueError(f"Unexpected 'related' kwarg provided for {message_type}") from None
            return {}
        else:
            if not related:
                raise ValueError(f"{message_type} expects a 'related' kwarg")
            return {neat_name: related}

    def recipients(self, message_type, **kwargs):
        raise NotImplementedError()

    def batch_recipients(self, message_type, sources, **kwargs):
        # Default batch recipients is to send a message to each of the recipients that would
        # receive a message under normal conditions
        return [
            {
                'recipients': self.recipients(message_type, source=source, **kwargs),
                'sources': [source]
            }
            for source in sources
        ]

    def process_batch(self, message_type, events, request, user, sources, related=None, **kwargs):
        events_by_source = {
            event.source.id: event
            for event in events
        }
        for recipient in self.batch_recipients(message_type, sources, user=user, **kwargs):
            recipients = recipient['recipients']
            sources = recipient['sources']
            events = [events_by_source[source.id] for source in sources]
            self.process_send(message_type, recipients, events, request, user, sources=sources, source=None, related=related, **kwargs)

    def process(self, message_type, event, request, user, source, related=None, **kwargs):
        recipients = self.recipients(message_type, source=source, related=related, user=user, **kwargs)
        self.process_send(message_type, recipients, [event], request, user, source, related=related, **kwargs)

    def process_send(self, message_type, recipients, events, request, user, source, sources=list(), related=None, **kwargs):
        try:
            # If this was a batch action we want to pull out the submission
            source = sources[0]
        except IndexError:
            pass

        kwargs = {
            'request': request,
            'user': user,
            'source': source,
            'sources': sources,
            'related': related,
            **kwargs,
        }
        kwargs.update(self.get_neat_related(message_type, related))
        kwargs.update(self.extra_kwargs(message_type, **kwargs))

        message = self.message(message_type, **kwargs)
        if not message:
            return

        for recipient in recipients:
            message_logs = self.create_logs(message, recipient, *events)

            if settings.SEND_MESSAGES or self.always_send:
                status = self.send_message(message, recipient=recipient, logs=message_logs, **kwargs)
            else:
                status = 'Message not sent as SEND_MESSAGES==FALSE'

            message_logs.update_status(status)

            if not settings.SEND_MESSAGES:
                if recipient:
                    debug_message = '{} [to: {}]: {}'.format(self.adapter_type, recipient, message)
                else:
                    debug_message = '{}: {}'.format(self.adapter_type, message)
                messages.add_message(request, messages.DEBUG, debug_message)

    def create_logs(self, message, recipient, *events):
        from .models import Message
        messages = Message.objects.bulk_create(
            Message(
                **self.log_kwargs(message, recipient, event)
            )
            for event in events
        )
        return Message.objects.filter(id__in=[message.id for message in messages])

    def log_kwargs(self, message, recipient, event):
        return {
            'type': self.adapter_type,
            'content': message,
            'recipient': recipient or '',
            'event': event,
        }

    def send_message(self, message, **kwargs):
        # Process the message, should return the result of the send
        # Returning None will not record this action
        raise NotImplementedError()


class ActivityAdapter(AdapterBase):
    adapter_type = "Activity Feed"
    always_send = True
    messages = {
        MESSAGES.TRANSITION: 'handle_transition',
        MESSAGES.BATCH_TRANSITION: 'handle_batch_transition',
        MESSAGES.NEW_SUBMISSION: _('Submitted {source.title} for {source.page.title}'),
        MESSAGES.EDIT: _('Edited'),
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
        MESSAGES.REVIEW_OPINION: _('{user} {opinion.opinion_display}s with {opinion.review.author}''s review of {source}'),
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
        MESSAGES.BATCH_DELETE_SUBMISSION: 'handle_batch_delete_submission'
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
        if is_transition(message_type) and not source.phase.permissions.can_view(source.user):
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
        base.extend([
            _('{user} as {name}.').format(user=str(user), name=role.name)
            for role, user in added
            if user
        ])
        return ' '.join(base)

    def batch_determination(self, sources, determinations, **kwargs):
        submission = sources[0]
        determination = determinations[submission.id]
        return self.messages[MESSAGES.DETERMINATION_OUTCOME].format(
            determination=determination,
        )

    def handle_batch_delete_submission(self, sources, **kwargs):
        submissions = sources
        submissions_text = ', '.join(
            [submission.title for submission in submissions]
        )
        return _('Successfully deleted submissions: {title}').format(title=submissions_text)

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
                old_phase = submission.workflow.previous_visible(old_phase, submission.user)

            applicant_message = base_message.format(
                old_display=old_phase.public_name,
                new_display=new_phase.public_name,
            )

            return json.dumps({
                TEAM: staff_message,
                ALL: applicant_message,
            })

        return staff_message

    def handle_batch_transition(self, transitions, sources, **kwargs):
        submissions = sources
        kwargs.pop('source')
        for submission in submissions:
            old_phase = transitions[submission.id]
            return self.handle_transition(old_phase=old_phase, source=submission, **kwargs)

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
        return _('Updated reporting frequency. New schedule is: {new_schedule} starting on {schedule_start}').format(new_schedule=new_schedule, schedule_start=config.schedule_start)

    def handle_skipped_report(self, report, **kwargs):
        if report.skipped:
            return "Skipped a Report"
        else:
            return "Marked a Report as required"

    def handle_update_invoice_status(self, invoice, **kwargs):
        invoice_status_change = _('Updated Invoice status to: {status}.').format(status=invoice.status_display)
        return invoice_status_change

    def send_message(self, message, user, source, sources, **kwargs):
        from .models import Activity
        visibility = kwargs.get('visibility', ALL)

        related = kwargs['related']
        if isinstance(related, dict):
            try:
                related = related[source.id]
            except KeyError:
                pass

        has_correct_fields = all(hasattr(related, attr) for attr in ['get_absolute_url'])
        isnt_source = source != related
        is_model = isinstance(related, models.Model)
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
        return _('Screening status from {old_status} to {new_status}').format(old_status=old_status, new_status=new_status)


class SlackAdapter(AdapterBase):
    adapter_type = "Slack"
    always_send = True
    messages = {
        MESSAGES.NEW_SUBMISSION: _('A new submission has been submitted for {source.page.title}: <{link}|{source.title}>'),
        MESSAGES.UPDATE_LEAD: _('The lead of <{link}|{source.title}> has been updated from {old_lead} to {source.lead} by {user}'),
        MESSAGES.BATCH_UPDATE_LEAD: 'handle_batch_lead',
        MESSAGES.COMMENT: _('A new {comment.visibility} comment has been posted on <{link}|{source.title}> by {user}'),
        MESSAGES.EDIT: _('{user} has edited <{link}|{source.title}>'),
        MESSAGES.APPLICANT_EDIT: _('{user} has edited <{link}|{source.title}>'),
        MESSAGES.REVIEWERS_UPDATED: 'reviewers_updated',
        MESSAGES.BATCH_REVIEWERS_UPDATED: 'handle_batch_reviewers',
        MESSAGES.PARTNERS_UPDATED: _('{user} has updated the partners on <{link}|{source.title}>'),
        MESSAGES.TRANSITION: _('{user} has updated the status of <{link}|{source.title}>: {old_phase.display_name} → {source.phase}'),
        MESSAGES.BATCH_TRANSITION: 'handle_batch_transition',
        MESSAGES.DETERMINATION_OUTCOME: 'handle_determination',
        MESSAGES.BATCH_DETERMINATION_OUTCOME: 'handle_batch_determination',
        MESSAGES.PROPOSAL_SUBMITTED: _('A proposal has been submitted for review: <{link}|{source.title}>'),
        MESSAGES.INVITED_TO_PROPOSAL: _('<{link}|{source.title}> by {source.user} has been invited to submit a proposal'),
        MESSAGES.NEW_REVIEW: _('{user} has submitted a review for <{link}|{source.title}>. Outcome: {review.outcome},  Score: {review.get_score_display}'),
        MESSAGES.READY_FOR_REVIEW: 'notify_reviewers',
        MESSAGES.OPENED_SEALED: _('{user} has opened the sealed submission: <{link}|{source.title}>'),
        MESSAGES.REVIEW_OPINION: _('{user} {opinion.opinion_display}s with {opinion.review.author}''s review of {source.title}'),
        MESSAGES.BATCH_READY_FOR_REVIEW: 'batch_notify_reviewers',
        MESSAGES.DELETE_SUBMISSION: _('{user} has deleted {source.title}'),
        MESSAGES.DELETE_REVIEW: _('{user} has deleted {review.author} review for <{link}|{source.title}>.'),
        MESSAGES.CREATED_PROJECT: _('{user} has created a Project: <{link}|{source.title}>.'),
        MESSAGES.UPDATE_PROJECT_LEAD: _('The lead of project <{link}|{source.title}> has been updated from {old_lead} to {source.lead} by {user}'),
        MESSAGES.EDIT_REVIEW: _('{user} has edited {review.author} review for <{link}|{source.title}>.'),
        MESSAGES.SEND_FOR_APPROVAL: _('{user} has requested approval on project <{link}|{source.title}>.'),
        MESSAGES.APPROVE_PROJECT: _('{user} has approved project <{link}|{source.title}>.'),
        MESSAGES.REQUEST_PROJECT_CHANGE: _('{user} has requested changes for project acceptance on <{link}|{source.title}>.'),
        MESSAGES.UPLOAD_CONTRACT: _('{user} has uploaded a contract for <{link}|{source.title}>.'),
        MESSAGES.APPROVE_CONTRACT: _('{user} has approved contract for <{link}|{source.title}>.'),
        MESSAGES.CREATE_INVOICE: _('{user} has created invoice for <{link}|{source.title}>.'),
        MESSAGES.UPDATE_INVOICE_STATUS: _('{user} has changed the status of <{link_related}|invoice> on <{link}|{source.title}> to {invoice.status_display}.'),
        MESSAGES.DELETE_INVOICE: _('{user} has deleted invoice from <{link}|{source.title}>.'),
        MESSAGES.UPDATE_INVOICE: _('{user} has updated invoice for <{link}|{source.title}>.'),
        MESSAGES.SUBMIT_REPORT: _('{user} has submitted a report for <{link}|{source.title}>.'),
        MESSAGES.BATCH_DELETE_SUBMISSION: 'handle_batch_delete_submission'
    }

    def __init__(self):
        super().__init__()
        self.destination = settings.SLACK_DESTINATION_URL
        self.target_room = settings.SLACK_DESTINATION_ROOM
        self.comments_room = settings.SLACK_DESTINATION_ROOM_COMMENTS
        self.comments_type = settings.SLACK_TYPE_COMMENTS

    def slack_links(self, links, sources):
        return ', '.join(
            f'<{links[source.id]}|{source.title}>'
            for source in sources
        )

    def extra_kwargs(self, message_type, **kwargs):
        source = kwargs['source']
        sources = kwargs['sources']
        request = kwargs['request']
        related = kwargs['related']
        link = link_to(source, request)
        link_related = link_to(related, request)
        links = {
            source.id: link_to(source, request)
            for source in sources
        }
        return {
            'link': link,
            'link_related': link_related,
            'links': links,
        }

    def recipients(self, message_type, source, related, **kwargs):
        if message_type == MESSAGES.SEND_FOR_APPROVAL:
            return [
                self.slack_id(user)
                for user in User.objects.approvers()
                if self.slack_id(user)
            ]

        recipients = [self.slack_id(source.lead)]

        # Notify second reviewer when first reviewer is done.
        if message_type == MESSAGES.NEW_REVIEW and related:
            submission = source
            if submission.assigned.with_roles().count() == 2 and related.author.reviewer == submission.assigned.with_roles().first().reviewer:
                recipients.append(self.slack_id(submission.assigned.with_roles().last().reviewer))

        return recipients

    def batch_recipients(self, message_type, sources, **kwargs):
        # We group the messages by lead
        leads = User.objects.filter(id__in=sources.values('lead'))
        return [
            {
                'recipients': [self.slack_id(lead)],
                'sources': sources.filter(lead=lead),
            } for lead in leads
        ]

    def reviewers_updated(self, source, link, user, added=list(), removed=list(), **kwargs):
        submission = source
        message = [_('{user} has updated the reviewers on <{link}|{title}>.').format(user=user, link=link, title=submission.title)]

        if added:
            message.append(_('Added:'))
            message.extend(reviewers_message(added))

        if removed:
            message.append(_('Removed:'))
            message.extend(reviewers_message(removed))

        return ' '.join(message)

    def handle_batch_lead(self, sources, links, user, new_lead, **kwargs):
        submissions = sources
        submissions_text = self.slack_links(links, submissions)
        return (
            _('{user} has batch changed lead to {new_lead} on: {submissions_text}').format(
                user=user,
                submissions_text=submissions_text,
                new_lead=new_lead,
            )
        )

    def handle_batch_reviewers(self, sources, links, user, added, **kwargs):
        submissions = sources
        submissions_text = self.slack_links(links, submissions)
        reviewers_text = ' '.join([
            _('{user} as {name},').format(user=str(user), name=role.name)
            for role, user in added
            if user
        ])
        return (
            _('{user} has batch added {reviewers_text} as reviewers on: {submissions_text}').format(
                user=user,
                submissions_text=submissions_text,
                reviewers_text=reviewers_text,
            )
        )

    def handle_batch_transition(self, user, links, sources, transitions, **kwargs):
        submissions = sources
        submissions_text = [
            ': '.join([
                self.slack_links(links, [submission]),
                f'{transitions[submission.id].display_name} → {submission.phase}',
            ])
            for submission in submissions
        ]
        submissions_links = ','.join(submissions_text)
        return (
            _('{user} has transitioned the following submissions: {submissions_links}').format(
                user=user,
                submissions_links=submissions_links,
            )
        )

    def handle_determination(self, source, link, determination, **kwargs):
        submission = source
        if determination.send_notice:
            return(
                _('A determination for <{link}|{submission_title}> was sent by email. Outcome: {determination_outcome}').format(
                    link=link,
                    submission_title=submission.title,
                    determination_outcome=determination.clean_outcome
                )
            )
        return (
            _('A determination for <{link}|{submission_title}> was saved without sending an email. Outcome: {determination_outcome}').format(
                link=link,
                submission_title=submission.title,
                determination_outcome=determination.clean_outcome
            )
        )

    def handle_batch_determination(self, sources, links, determinations, **kwargs):
        submissions = sources
        submissions_links = ','.join([
            self.slack_links(links, [submission])
            for submission in submissions
        ])

        outcome = determinations[submissions[0].id].clean_outcome

        return (
            _('Determinations of {outcome} was sent for: {submissions_links}').format(
                outcome=outcome,
                submissions_links=submissions_links,
            )
        )

    def handle_batch_delete_submission(self, sources, links, user, **kwargs):
        submissions = sources
        submissions_text = ', '.join([submission.title for submission in submissions])
        return _('{user} has deleted submissions: {title}').format(user=user, title=submissions_text)

    def notify_reviewers(self, source, link, **kwargs):
        submission = source
        reviewers_to_notify = []
        for reviewer in submission.reviewers.all():
            if submission.phase.permissions.can_review(reviewer):
                reviewers_to_notify.append(reviewer)

        reviewers = ', '.join(
            str(reviewer) for reviewer in reviewers_to_notify
        )

        return (
            _('<{link}|{title}> is ready for review. The following are assigned as reviewers: {reviewers}').format(
                link=link,
                reviewers=reviewers,
                title=submission.title,
            )
        )

    def batch_notify_reviewers(self, sources, links, **kwargs):
        kwargs.pop('source')
        kwargs.pop('link')
        return '. '.join(
            self.notify_reviewers(source, link=links[source.id], **kwargs)
            for source in sources
        )

    def slack_id(self, user):
        if user is None:
            return ''

        if not user.slack:
            return ''

        return f'<{user.slack}>'

    def slack_channels(self, source, **kwargs):
        # Set the default room as a start.
        target_rooms = [self.target_room]
        try:
            fund_slack_channel = source.get_from_parent('slack_channel').split(',')
        except AttributeError:
            # Not a submission object.
            pass
        else:
            # If there are custom rooms, set them in place of the default room
            custom_rooms = [channel for channel in fund_slack_channel if channel]
            if len(custom_rooms) > 0:
                target_rooms = custom_rooms

        try:
            comment = kwargs['comment']
        except KeyError:
            # Not a comment, no extra rooms.
            pass
        else:
            if self.comments_room:
                if any(self.comments_type):
                    if comment.visibility in self.comments_type:
                        target_rooms.extend([self.comments_room])
                else:
                    target_rooms.extend([self.comments_room])

        # Make sure each channel name starts with a "#".
        target_rooms = [
            room.strip() if room.startswith('#') else '#' + room.strip()
            for room in target_rooms
            if room
        ]

        return target_rooms

    def send_message(self, message, recipient, source, **kwargs):
        target_rooms = self.slack_channels(source, **kwargs)

        if not self.destination or not any(target_rooms):
            errors = list()
            if not self.destination:
                errors.append('Destination URL')
            if not target_rooms:
                errors.append('Room ID')
            return 'Missing configuration: {}'.format(', '.join(errors))

        message = ' '.join([recipient, message]).strip()

        data = {
            "room": target_rooms,
            "message": message,
        }
        response = requests.post(self.destination, json=data)

        return str(response.status_code) + ': ' + response.content.decode()


class EmailAdapter(AdapterBase):
    adapter_type = 'Email'
    messages = {
        MESSAGES.NEW_SUBMISSION: 'funds/email/confirmation.html',
        MESSAGES.COMMENT: 'notify_comment',
        MESSAGES.EDIT: 'messages/email/edit.html',
        MESSAGES.TRANSITION: 'handle_transition',
        MESSAGES.BATCH_TRANSITION: 'handle_batch_transition',
        MESSAGES.DETERMINATION_OUTCOME: 'handle_determination',
        MESSAGES.BATCH_DETERMINATION_OUTCOME: 'handle_batch_determination',
        MESSAGES.INVITED_TO_PROPOSAL: 'messages/email/invited_to_proposal.html',
        MESSAGES.BATCH_READY_FOR_REVIEW: 'handle_batch_ready_for_review',
        MESSAGES.READY_FOR_REVIEW: 'handle_ready_for_review',
        MESSAGES.REVIEWERS_UPDATED: 'handle_ready_for_review',
        MESSAGES.BATCH_REVIEWERS_UPDATED: 'handle_batch_ready_for_review',
        MESSAGES.PARTNERS_UPDATED: 'partners_updated_applicant',
        MESSAGES.PARTNERS_UPDATED_PARTNER: 'partners_updated_partner',
        MESSAGES.UPLOAD_CONTRACT: 'messages/email/contract_uploaded.html',
        MESSAGES.CREATED_PROJECT: 'handle_project_created',
        MESSAGES.UPDATED_VENDOR: 'handle_vendor_updated',
        MESSAGES.SENT_TO_COMPLIANCE: 'messages/email/sent_to_compliance.html',
        MESSAGES.UPDATE_INVOICE: 'handle_invoice_updated',
        MESSAGES.UPDATE_INVOICE_STATUS: 'handle_invoice_status_updated',
        MESSAGES.SUBMIT_REPORT: 'messages/email/report_submitted.html',
        MESSAGES.SKIPPED_REPORT: 'messages/email/report_skipped.html',
        MESSAGES.REPORT_FREQUENCY_CHANGED: 'messages/email/report_frequency.html',
        MESSAGES.REPORT_NOTIFY: 'messages/email/report_notify.html',
        MESSAGES.REVIEW_REMINDER: 'messages/email/ready_to_review.html',
    }

    def get_subject(self, message_type, source):
        if source:
            if is_ready_for_review(message_type) or is_reviewer_update(message_type):
                subject = _('Application ready to review: {source.title}').format(source=source)
                if message_type in {MESSAGES.BATCH_READY_FOR_REVIEW, MESSAGES.BATCH_REVIEWERS_UPDATED}:
                    subject = _('Multiple applications are now ready for your review')
            elif message_type in {MESSAGES.REVIEW_REMINDER}:
                subject = _('Reminder: Application ready to review: {source.title}').format(source=source)
            else:
                try:
                    subject = source.page.specific.subject or _('Your application to {org_long_name}: {source.title}').format(org_long_name=settings.ORG_LONG_NAME, source=source)
                except AttributeError:
                    subject = _('Your {org_long_name} Project: {source.title}').format(org_long_name=settings.ORG_LONG_NAME, source=source)
            return subject

    def extra_kwargs(self, message_type, source, sources, **kwargs):
        return {
            'subject': self.get_subject(message_type, source),
        }

    def handle_transition(self, old_phase, source, **kwargs):
        from hypha.apply.funds.workflow import PHASES
        submission = source
        # Retrive status index to see if we are going forward or backward.
        old_index = list(dict(PHASES).keys()).index(old_phase.name)
        target_index = list(dict(PHASES).keys()).index(submission.status)
        is_forward = old_index < target_index

        if is_forward:
            return self.render_message(
                'messages/email/transition.html',
                source=submission,
                old_phase=old_phase,
                **kwargs
            )

    def handle_batch_transition(self, transitions, sources, **kwargs):
        submissions = sources
        kwargs.pop('source')
        for submission in submissions:
            old_phase = transitions[submission.id]
            return self.handle_transition(old_phase=old_phase, source=submission, **kwargs)

    def handle_invoice_status_updated(self, related, **kwargs):
        return self.render_message(
            'messages/email/invoice_status_updated.html',
            has_changes_requested=related.has_changes_requested,
            **kwargs,
        )

    def handle_invoice_updated(self, **kwargs):
        return self.render_message(
            'messages/email/invoice_updated.html',
            **kwargs,
        )

    def handle_project_created(self, source, **kwargs):
        from hypha.apply.projects.models import ProjectSettings
        request = kwargs.get('request')
        project_settings = ProjectSettings.for_request(request)
        if project_settings.vendor_setup_required:
            return self.render_message(
                'messages/email/vendor_setup_needed.html',
                source=source,
                **kwargs
            )

    def handle_vendor_updated(self, source, **kwargs):
        return self.render_message(
            'messages/email/vendor_updated.html',
            source=source,
            **kwargs,
        )

    def handle_determination(self, determination, source, **kwargs):
        submission = source
        if determination.send_notice:
            return self.render_message(
                'messages/email/determination.html',
                source=submission,
                determination=determination,
                **kwargs
            )

    def handle_batch_determination(self, determinations, sources, **kwargs):
        submissions = sources
        kwargs.pop('source')
        for submission in submissions:
            determination = determinations[submission.id]
            return self.render_message(
                'messages/email/determination.html',
                source=submission,
                determination=determination,
                **kwargs
            )

    def handle_ready_for_review(self, request, source, **kwargs):
        if settings.SEND_READY_FOR_REVIEW:
            return self.render_message(
                'messages/email/ready_to_review.html',
                source=source,
                request=request,
                **kwargs
            )

    def handle_batch_ready_for_review(self, request, sources, **kwargs):
        if settings.SEND_READY_FOR_REVIEW:
            return self.render_message(
                'messages/email/batch_ready_to_review.html',
                sources=sources,
                request=request,
                **kwargs
            )

    def notify_comment(self, **kwargs):
        comment = kwargs['comment']
        source = kwargs['source']
        if not comment.priviledged and not comment.user == source.user:
            return self.render_message('messages/email/comment.html', **kwargs)

    def recipients(self, message_type, source, related, user, **kwargs):
        if is_ready_for_review(message_type):
            return self.reviewers(source)

        if is_reviewer_update(message_type):
            # Notify newly added reviewers only if they can review in the current phase
            reviewers = self.reviewers(source)
            added = kwargs.get("added", [])
            return [
                assigned_reviewer.reviewer.email
                for assigned_reviewer in added
                if assigned_reviewer.reviewer.email in reviewers
            ]

        if is_transition(message_type):
            # Only notify the applicant if the new phase can be seen within the workflow
            if not source.phase.permissions.can_view(source.user):
                return []

        if message_type == MESSAGES.PARTNERS_UPDATED_PARTNER:
            partners = kwargs['added']
            return [partner.email for partner in partners]

        if message_type == MESSAGES.SENT_TO_COMPLIANCE:
            from hypha.apply.projects.models import ProjectSettings
            project_settings = ProjectSettings.objects.first()

            if project_settings is None:
                # TODO: what to do when this isn't configured??
                return []

            return [project_settings.compliance_email]

        if message_type in {MESSAGES.SUBMIT_REPORT, MESSAGES.UPDATE_INVOICE}:
            # Don't tell the user if they did these activities
            if user.is_applicant:
                return []

        if message_type in {MESSAGES.REVIEW_REMINDER}:
            return self.reviewers(source)

        if message_type in {MESSAGES.UPDATE_INVOICE_STATUS}:
            if related.status in  ['changes_requested_by_finance1', 'approved_by_finance1']:
                return [related.project.lead.email]
            if related.status in  ['changes_requested', 'approved_by_staff']:
                return [related.by.email]
            if related.status in  ['submitted', 'Resubmitted']:
                return [related.project.lead.email]
            return [user.email]

        return [source.user.email]

    def batch_recipients(self, message_type, sources, **kwargs):
        if not (is_ready_for_review(message_type) or is_reviewer_update(message_type)):
            return super().batch_recipients(message_type, sources, **kwargs)

        added = [reviewer.email for _, reviewer in kwargs.get("added", []) if reviewer]

        reviewers_to_message = defaultdict(list)
        for source in sources:
            reviewers = self.reviewers(source)
            for reviewer in reviewers:
                if not is_reviewer_update(message_type) or reviewer in added:
                    reviewers_to_message[reviewer].append(source)

        return [
            {
                'recipients': [reviewer],
                'sources': sources,
            } for reviewer, sources in reviewers_to_message.items()
        ]

    def reviewers(self, source):
        return [
            reviewer.email
            for reviewer in source.missing_reviewers.all()
            if source.phase.permissions.can_review(reviewer) and not reviewer.is_apply_staff
        ]

    def partners_updated_applicant(self, added, removed, **kwargs):
        if added:
            return self.render_message(
                'messages/email/partners_update_applicant.html',
                added=added,
                **kwargs
            )

    def partners_updated_partner(self, added, removed, **kwargs):
        for partner in added:
            return self.render_message('messages/email/partners_update_partner.html', **kwargs)

    def render_message(self, template, **kwargs):
        return render_to_string(template, kwargs, kwargs['request'])

    def send_message(self, message, source, subject, recipient, logs, **kwargs):
        try:
            from_email = source.page.specific.from_address
        except AttributeError:  # we're dealing with a project
            from_email = source.submission.page.specific.from_address
        except Exception as e:
            from_email = None
            logger.exception(e)

        try:
            send_mail(
                subject,
                message,
                from_email,
                [recipient],
                logs=logs
            )
        except Exception as e:
            return 'Error: ' + str(e)


class DjangoMessagesAdapter(AdapterBase):
    adapter_type = 'Django'
    always_send = True

    messages = {
        MESSAGES.BATCH_REVIEWERS_UPDATED: 'batch_reviewers_updated',
        MESSAGES.BATCH_TRANSITION: 'batch_transition',
        MESSAGES.BATCH_DETERMINATION_OUTCOME: 'batch_determinations',
        MESSAGES.UPLOAD_DOCUMENT: _('Successfully uploaded document'),
        MESSAGES.REMOVE_DOCUMENT: _('Successfully removed document'),
        MESSAGES.SKIPPED_REPORT: 'handle_skipped_report',
        MESSAGES.REPORT_FREQUENCY_CHANGED: 'handle_report_frequency',
        MESSAGES.CREATE_REMINDER: _('Reminder created'),
        MESSAGES.DELETE_REMINDER: _('Reminder deleted'),
    }

    def batch_reviewers_updated(self, added, sources, **kwargs):
        reviewers_text = ' '.join([
            _('{user} as {name},').format(user=str(user), name=role.name)
            for role, user in added
            if user
        ])

        return (
            _('Batch reviewers added: {reviewers_text} to ').format(reviewers_text=reviewers_text) + ', '.join(['"{title}"'.format(title=source.title) for source in sources])
        )

    def handle_report_frequency(self, config, **kwargs):
        new_schedule = config.get_frequency_display()
        return _('Successfully updated reporting frequency. They will now report {new_schedule} starting on {schedule_start}').format(new_schedule=new_schedule, schedule_start=config.schedule_start)

    def handle_skipped_report(self, report, **kwargs):
        if report.skipped:
            return _('Successfully skipped a Report for {start_date} to {end_date}').format(start_date=report.start_date, end_date=report.end_date)
        else:
            return _('Successfully unskipped a Report for {start_date} to {end_date}').format(start_date=report.start_date, end_date=report.end_date)

    def batch_transition(self, sources, transitions, **kwargs):
        base_message = 'Successfully updated:'
        transition = '{submission} [{old_display} → {new_display}].'
        transition_messages = [
            transition.format(
                submission=submission.title,
                old_display=transitions[submission.id],
                new_display=submission.phase,
            ) for submission in sources
        ]
        messages = [base_message, *transition_messages]
        return ' '.join(messages)

    def batch_determinations(self, sources, determinations, **kwargs):
        submissions = sources
        outcome = determinations[submissions[0].id].clean_outcome

        base_message = _('Successfully determined as {outcome}: ').format(outcome=outcome)
        submissions_text = [
            str(submission.title) for submission in submissions
        ]
        return base_message + ', '.join(submissions_text)

    def recipients(self, *args, **kwargs):
        return [None]

    def batch_recipients(self, message_type, sources, *args, **kwargs):
        return [{
            'recipients': [None],
            'sources': sources,
        }]

    def send_message(self, message, request, **kwargs):
        messages.add_message(request, messages.INFO, message)


class MessengerBackend:
    def __init__(self, *adpaters):
        self.adapters = adpaters

    def __call__(self, *args, related=None, **kwargs):
        return self.send(*args, related=related, **kwargs)

    def send(self, message_type, request, user, related, source=None, sources=list(), **kwargs):
        from .models import Event
        if source:
            event = Event.objects.create(type=message_type.name, by=user, source=source)
            for adapter in self.adapters:
                adapter.process(message_type, event, request=request, user=user, source=source, related=related, **kwargs)

        elif sources:
            events = Event.objects.bulk_create(
                Event(type=message_type.name, by=user, source=source)
                for source in sources
            )
            for adapter in self.adapters:
                adapter.process_batch(message_type, events, request=request, user=user, sources=sources, related=related, **kwargs)


adapters = [
    ActivityAdapter(),
    SlackAdapter(),
    EmailAdapter(),
    DjangoMessagesAdapter(),
]


messenger = MessengerBackend(*adapters)
