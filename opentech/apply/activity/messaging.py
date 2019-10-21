import json
import requests
from collections import defaultdict

from django.db import models
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.utils import timezone

from .models import TEAM, ALL
from .options import MESSAGES
from .tasks import send_mail


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
            message += ' as ' + str(role)
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
    MESSAGES.REQUEST_PAYMENT: 'payment_request',
    MESSAGES.UPDATE_PAYMENT_REQUEST_STATUS: 'payment_request',
    MESSAGES.DELETE_PAYMENT_REQUEST: 'payment_request',
    MESSAGES.UPDATE_PAYMENT_REQUEST: 'payment_request',
}


def is_transition(message_type):
    return message_type in [MESSAGES.TRANSITION, MESSAGES.BATCH_TRANSITION]


def is_ready_for_review(message_type):
    return message_type in [MESSAGES.READY_FOR_REVIEW, MESSAGES.BATCH_READY_FOR_REVIEW]


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
        for recipient in self.batch_recipients(message_type, sources, **kwargs):
            recipients = recipient['recipients']
            sources = recipient['sources']
            events = [events_by_source[source.id] for source in sources]
            self.process_send(message_type, recipients, events, request, user, sources=sources, source=None, related=related, **kwargs)

    def process(self, message_type, event, request, user, source, related=None, **kwargs):
        recipients = self.recipients(message_type, source=source, related=related, **kwargs)
        self.process_send(message_type, recipients, [event], request, user, source, related=related, **kwargs)

    def process_send(self, message_type, recipients, events, request, user, source, sources=list(), related=None, **kwargs):
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
        MESSAGES.NEW_SUBMISSION: 'Submitted {source.title} for {source.page.title}',
        MESSAGES.EDIT: 'Edited',
        MESSAGES.APPLICANT_EDIT: 'Edited',
        MESSAGES.UPDATE_LEAD: 'Lead changed from {old_lead} to {source.lead}',
        MESSAGES.BATCH_UPDATE_LEAD: 'Batch Lead changed to {new_lead}',
        MESSAGES.DETERMINATION_OUTCOME: 'Sent a determination. Outcome: {determination.clean_outcome}',
        MESSAGES.BATCH_DETERMINATION_OUTCOME: 'batch_determination',
        MESSAGES.INVITED_TO_PROPOSAL: 'Invited to submit a proposal',
        MESSAGES.REVIEWERS_UPDATED: 'reviewers_updated',
        MESSAGES.BATCH_REVIEWERS_UPDATED: 'batch_reviewers_updated',
        MESSAGES.PARTNERS_UPDATED: 'partners_updated',
        MESSAGES.NEW_REVIEW: 'Submitted a review',
        MESSAGES.OPENED_SEALED: 'Opened the submission while still sealed',
        MESSAGES.SCREENING: 'Screening status from {old_status} to {source.screening_status}',
        MESSAGES.REVIEW_OPINION: '{user} {opinion.opinion_display}s with {opinion.review.author}''s review of {source}',
        MESSAGES.CREATED_PROJECT: 'Created',
        MESSAGES.PROJECT_TRANSITION: 'Progressed from {old_stage} to {source.status_display}',
        MESSAGES.UPDATE_PROJECT_LEAD: 'Lead changed from {old_lead} to {source.lead}',
        MESSAGES.SEND_FOR_APPROVAL: 'Requested approval',
        MESSAGES.APPROVE_PROJECT: 'Approved',
        MESSAGES.REQUEST_PROJECT_CHANGE: 'Requested changes for acceptance: "{comment}"',
        MESSAGES.UPLOAD_CONTRACT: 'Uploaded a {contract.state} contract',
        MESSAGES.APPROVE_CONTRACT: 'Approved contract',
        MESSAGES.UPDATE_PAYMENT_REQUEST_STATUS: 'Updated Payment Request status to: {payment_request.status_display}',
        MESSAGES.REQUEST_PAYMENT: 'Payment Request submitted',
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
        ]:
            return {'visibility': TEAM}

        source = source or sources[0]
        if is_transition(message_type) and not source.phase.permissions.can_view(source.user):
            # User's shouldn't see status activity changes for stages that aren't visible to the them
            return {'visibility': TEAM}
        return {}

    def reviewers_updated(self, added=list(), removed=list(), **kwargs):
        message = ['Reviewers updated.']
        if added:
            message.append('Added:')
            message.extend(reviewers_message(added))

        if removed:
            message.append('Removed:')
            message.extend(reviewers_message(removed))

        return ' '.join(message)

    def batch_reviewers_updated(self, added, **kwargs):
        base = ['Batch Reviewers Updated.']
        base.extend([
            f'{str(user)} as {role.name}.'
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

    def handle_transition(self, old_phase, source, **kwargs):
        submission = source
        base_message = 'Progressed from {old_display} to {new_display}'

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
        message = ['Partners updated.']
        if added:
            message.append('Added:')
            message.append(', '.join([str(user) for user in added]) + '.')

        if removed:
            message.append('Removed:')
            message.append(', '.join([str(user) for user in removed]) + '.')

        return ' '.join(message)

    def send_message(self, message, user, source, sources, **kwargs):
        from .models import Activity
        visibility = kwargs.get('visibility', ALL)

        try:
            # If this was a batch action we want to pull out the submission
            source = sources[0]
        except IndexError:
            pass

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


class SlackAdapter(AdapterBase):
    adapter_type = "Slack"
    always_send = True
    messages = {
        MESSAGES.NEW_SUBMISSION: 'A new submission has been submitted for {source.page.title}: <{link}|{source.title}>',
        MESSAGES.UPDATE_LEAD: 'The lead of <{link}|{source.title}> has been updated from {old_lead} to {source.lead} by {user}',
        MESSAGES.BATCH_UPDATE_LEAD: 'handle_batch_lead',
        MESSAGES.COMMENT: 'A new {comment.visibility} comment has been posted on <{link}|{source.title}> by {user}',
        MESSAGES.EDIT: '{user} has edited <{link}|{source.title}>',
        MESSAGES.APPLICANT_EDIT: '{user} has edited <{link}|{source.title}>',
        MESSAGES.REVIEWERS_UPDATED: 'reviewers_updated',
        MESSAGES.BATCH_REVIEWERS_UPDATED: 'handle_batch_reviewers',
        MESSAGES.PARTNERS_UPDATED: '{user} has updated the partners on <{link}|{source.title}>',
        MESSAGES.TRANSITION: '{user} has updated the status of <{link}|{source.title}>: {old_phase.display_name} → {source.phase}',
        MESSAGES.BATCH_TRANSITION: 'handle_batch_transition',
        MESSAGES.DETERMINATION_OUTCOME: 'A determination for <{link}|{source.title}> was sent by email. Outcome: {determination.clean_outcome}',
        MESSAGES.BATCH_DETERMINATION_OUTCOME: 'handle_batch_determination',
        MESSAGES.PROPOSAL_SUBMITTED: 'A proposal has been submitted for review: <{link}|{source.title}>',
        MESSAGES.INVITED_TO_PROPOSAL: '<{link}|{source.title}> by {source.user} has been invited to submit a proposal',
        MESSAGES.NEW_REVIEW: '{user} has submitted a review for <{link}|{source.title}>. Outcome: {review.outcome},  Score: {review.get_score_display}',
        MESSAGES.READY_FOR_REVIEW: 'notify_reviewers',
        MESSAGES.OPENED_SEALED: '{user} has opened the sealed submission: <{link}|{source.title}>',
        MESSAGES.REVIEW_OPINION: '{user} {opinion.opinion_display}s with {opinion.review.author}''s review of {source.title}',
        MESSAGES.BATCH_READY_FOR_REVIEW: 'batch_notify_reviewers',
        MESSAGES.DELETE_SUBMISSION: '{user} has deleted {source.title}',
        MESSAGES.DELETE_REVIEW: '{user} has deleted {review.author} review for <{link}|{source.title}>.',
        MESSAGES.CREATED_PROJECT: '{user} has created a Project: <{link}|{source.title}>.',
        MESSAGES.UPDATE_PROJECT_LEAD: 'The lead of project <{link}|{source.title}> has been updated from {old_lead} to {source.lead} by {user}',
        MESSAGES.EDIT_REVIEW: '{user} has edited {review.author} review for <{link}|{source.title}>.',
        MESSAGES.SEND_FOR_APPROVAL: '{user} has requested approval on project <{link}|{source.title}>.',
        MESSAGES.APPROVE_PROJECT: '{user} has approved project <{link}|{source.title}>.',
        MESSAGES.REQUEST_PROJECT_CHANGE: '{user} has requested changes for project acceptance on <{link}|{source.title}>.',
        MESSAGES.UPLOAD_CONTRACT: '{user} has uploaded a contract for <{link}|{source.title}>.',
        MESSAGES.APPROVE_CONTRACT: '{user} has approved contract for <{link}|{source.title}>.',
        MESSAGES.REQUEST_PAYMENT: '{user} has requested payment for <{link}|{source.title}>.',
        MESSAGES.UPDATE_PAYMENT_REQUEST_STATUS: '{user} has changed the status of <{link_related}|payment request> on <{link}|{source.title}> to {payment_request.status_display}.',
        MESSAGES.DELETE_PAYMENT_REQUEST: '{user} has deleted payment request from <{link}|{source.title}>.',
        MESSAGES.UPDATE_PAYMENT_REQUEST: '{user} has updated payment request for <{link}|{source.title}>.',
    }

    def __init__(self):
        super().__init__()
        self.destination = settings.SLACK_DESTINATION_URL
        self.target_room = settings.SLACK_DESTINATION_ROOM

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
        message = [f'{user} has updated the reviewers on <{link}|{submission.title}>.']

        if added:
            message.append('Added:')
            message.extend(reviewers_message(added))

        if removed:
            message.append('Removed:')
            message.extend(reviewers_message(removed))

        return ' '.join(message)

    def handle_batch_lead(self, sources, links, user, new_lead, **kwargs):
        submissions = sources
        submissions_text = self.slack_links(links, submissions)
        return (
            '{user} has batch changed lead to {new_lead} on: {submissions_text}'.format(
                user=user,
                submissions_text=submissions_text,
                new_lead=new_lead,
            )
        )

    def handle_batch_reviewers(self, sources, links, user, added, **kwargs):
        submissions = sources
        submissions_text = self.slack_links(links, submissions)
        reviewers_text = ' '.join([
            f'{str(user)} as {role.name},'
            for role, user in added
            if user
        ])
        return (
            '{user} has batch added {reviewers_text} as reviewers on: {submissions_text}'.format(
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
            '{user} has transitioned the following submissions: {submissions_links}'.format(
                user=user,
                submissions_links=submissions_links,
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
            'Determinations of {outcome} was sent for: {submissions_links}'.format(
                outcome=outcome,
                submissions_links=submissions_links,
            )
        )

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
            '<{link}|{submission.title}> is ready for review. The following are assigned as reviewers: {reviewers}'.format(
                link=link,
                reviewers=reviewers,
                submission=submission,
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

    def slack_channels(self, source):
        target_rooms = [self.target_room]
        try:
            extra_rooms = source.get_from_parent('slack_channel').split(',')
        except AttributeError:
            # Not a submission object, no extra rooms.
            pass
        else:
            target_rooms.extend(extra_rooms)

        # Make sure each channel name starts with a "#".
        target_rooms = [
            room if room.startswith('#') else '#' + room
            for room in target_rooms
            if room
        ]

        return target_rooms

    def send_message(self, message, recipient, source, **kwargs):
        target_rooms = self.slack_channels(source)

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
        MESSAGES.DETERMINATION_OUTCOME: 'messages/email/determination.html',
        MESSAGES.BATCH_DETERMINATION_OUTCOME: 'batch_determination',
        MESSAGES.INVITED_TO_PROPOSAL: 'messages/email/invited_to_proposal.html',
        MESSAGES.BATCH_READY_FOR_REVIEW: 'messages/email/batch_ready_to_review.html',
        MESSAGES.READY_FOR_REVIEW: 'messages/email/ready_to_review.html',
        MESSAGES.PARTNERS_UPDATED: 'partners_updated_applicant',
        MESSAGES.PARTNERS_UPDATED_PARTNER: 'partners_updated_partner',
        MESSAGES.UPLOAD_CONTRACT: 'messages/email/contract_uploaded.html',
        MESSAGES.SENT_TO_COMPLIANCE: 'messages/email/sent_to_compliance.html',
        MESSAGES.UPDATE_PAYMENT_REQUEST: 'handle_update_payment_request',
        MESSAGES.UPDATE_PAYMENT_REQUEST_STATUS: 'handle_payment_status_updated',
    }

    def get_subject(self, message_type, source):
        if source:
            if is_ready_for_review(message_type):
                subject = 'Application ready to review: {source.title}'.format(source=source)
            else:
                try:
                    subject = source.page.specific.subject or 'Your application to {org_long_name}: {source.title}'.format(org_long_name=settings.ORG_LONG_NAME, source=source)
                except AttributeError:
                    subject = 'Your {org_long_name} Project: {source.title}'.format(org_long_name=settings.ORG_LONG_NAME, source=source)
            return subject

    def extra_kwargs(self, message_type, source, sources, **kwargs):
        return {
            'subject': self.get_subject(message_type, source),
        }

    def handle_transition(self, old_phase, source, **kwargs):
        from opentech.apply.funds.workflow import PHASES
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

    def handle_update_payment_request(self, user, **kwargs):
        if user.is_applicant:
            return

        return self.render_message(
            'messages/email/payment_request_updated.html',
            **kwargs,
        )

    def handle_payment_status_updated(self, related, **kwargs):
        return self.render_message(
            'messages/email/payment_request_status_updated.html',
            has_changes_requested=related.has_changes_requested,
            **kwargs,
        )

    def batch_determination(self, determinations, sources, **kwargs):
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

    def notify_comment(self, **kwargs):
        comment = kwargs['comment']
        source = kwargs['source']
        if not comment.priviledged and not comment.user == source.user:
            return self.render_message('messages/email/comment.html', **kwargs)

    def recipients(self, message_type, source, **kwargs):
        if is_ready_for_review(message_type):
            return self.reviewers(source)

        if is_transition(message_type):
            # Only notify the applicant if the new phase can be seen within the workflow
            if not source.phase.permissions.can_view(source.user):
                return []

        if message_type == MESSAGES.PARTNERS_UPDATED_PARTNER:
            partners = kwargs['added']
            return [partner.email for partner in partners]

        if message_type == MESSAGES.SENT_TO_COMPLIANCE:
            from opentech.apply.projects.models import ProjectSettings
            project_settings = ProjectSettings.objects.first()

            if project_settings is None:
                # TODO: what to do when this isn't configured??
                return []

            return [project_settings.compliance_email]

        return [source.user.email]

    def batch_recipients(self, message_type, sources, **kwargs):
        if not is_ready_for_review(message_type):
            return super().batch_recipients(message_type, sources, **kwargs)

        reviewers_to_message = defaultdict(list)
        for source in sources:
            reviewers = self.reviewers(source)
            for reviewer in reviewers:
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
        return render_to_string(template, kwargs)

    def send_message(self, message, source, subject, recipient, logs, **kwargs):
        try:
            from_email = source.page.specific.from_address
        except AttributeError:  # we're dealing with a project
            from_email = source.submission.page.specific.from_address

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
        MESSAGES.UPLOAD_DOCUMENT: 'Successfully uploaded document',
        MESSAGES.REMOVE_DOCUMENT: 'Successfully removed document',
    }

    def batch_reviewers_updated(self, added, sources, **kwargs):
        reviewers_text = ' '.join([
            f'{str(user)} as {role.name},'
            for role, user in added
            if user
        ])

        return (
            'Batch reviewers added: ' +
            reviewers_text +
            ' to ' +
            ', '.join(['"{}"'.format(source.title) for source in sources])
        )

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

        base_message = f'Successfully determined as {outcome}: '
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
