import json
import requests
from collections import defaultdict

from django.db import models
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.utils import timezone

from opentech.apply.funds.workflow import PHASES

from .models import INTERNAL, PUBLIC
from .options import MESSAGES
from .tasks import send_mail


User = get_user_model()


def link_to(target, request):
    if target:
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
    MESSAGES.UPDATE_PROJECT_LEAD: 'old_lead',
    MESSAGES.EDIT_REVIEW: 'review',
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

    def batch_recipients(self, message_type, submissions, **kwargs):
        # Default batch recipients is to send a message to each of the recipients that would
        # receive a message under normal conditions
        return [
            {
                'recipients': self.recipients(message_type, submission=submission, **kwargs),
                'submissions': [submission]
            }
            for submission in submissions
        ]

    def process_batch(self, message_type, events, request, user, submissions, related=None, **kwargs):
        events_by_submission = {
            event.submission.id: event
            for event in events
        }
        for recipient in self.batch_recipients(message_type, submissions, **kwargs):
            recipients = recipient['recipients']
            submissions = recipient['submissions']
            events = [events_by_submission[submission.id] for submission in submissions]
            self.process_send(message_type, recipients, events, request, user, submissions=submissions, submission=None, related=related, **kwargs)

    def process(self, message_type, event, request, user, submission, related=None, **kwargs):
        recipients = self.recipients(message_type, submission=submission, related=related, **kwargs)
        self.process_send(message_type, recipients, [event], request, user, submission, related=related, **kwargs)

    def process_send(self, message_type, recipients, events, request, user, submission, submissions=list(), related=None, **kwargs):
        kwargs = {
            'request': request,
            'user': user,
            'submission': submission,
            'submissions': submissions,
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
        MESSAGES.NEW_SUBMISSION: 'Submitted {submission.title} for {submission.page.title}',
        MESSAGES.EDIT: 'Edited',
        MESSAGES.APPLICANT_EDIT: 'Edited',
        MESSAGES.UPDATE_LEAD: 'Lead changed from {old_lead} to {submission.lead}',
        MESSAGES.BATCH_UPDATE_LEAD: 'Batch Lead changed to {new_lead}',
        MESSAGES.DETERMINATION_OUTCOME: 'Sent a determination. Outcome: {determination.clean_outcome}',
        MESSAGES.BATCH_DETERMINATION_OUTCOME: 'batch_determination',
        MESSAGES.INVITED_TO_PROPOSAL: 'Invited to submit a proposal',
        MESSAGES.REVIEWERS_UPDATED: 'reviewers_updated',
        MESSAGES.BATCH_REVIEWERS_UPDATED: 'batch_reviewers_updated',
        MESSAGES.PARTNERS_UPDATED: 'partners_updated',
        MESSAGES.NEW_REVIEW: 'Submitted a review',
        MESSAGES.OPENED_SEALED: 'Opened the submission while still sealed',
        MESSAGES.SCREENING: 'Screening status from {old_status} to {submission.screening_status}',
        MESSAGES.REVIEW_OPINION: '{user} {opinion.opinion_display}s with {opinion.review.author}''s review of {submission}'
    }

    def recipients(self, message_type, **kwargs):
        return [None]

    def extra_kwargs(self, message_type, submission, submissions, **kwargs):
        from .models import INTERNAL
        if message_type in [
                MESSAGES.OPENED_SEALED,
                MESSAGES.REVIEWERS_UPDATED,
                MESSAGES.SCREENING,
                MESSAGES.REVIEW_OPINION,
                MESSAGES.BATCH_REVIEWERS_UPDATED,
                MESSAGES.PARTNERS_UPDATED,
        ]:
            return {'visibility': INTERNAL}

        submission = submission or submissions[0]
        if is_transition(message_type) and not submission.phase.permissions.can_view(submission.user):
            # User's shouldn't see status activity changes for stages that aren't visible to the them
            return {'visibility': INTERNAL}
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

    def batch_determination(self, submissions, determinations, **kwargs):
        submission = submissions[0]
        determination = determinations[submission.id]
        return self.messages[MESSAGES.DETERMINATION_OUTCOME].format(
            determination=determination,
            submission=submission,
        )

    def handle_transition(self, old_phase, submission, **kwargs):
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
                INTERNAL: staff_message,
                PUBLIC: applicant_message,
            })

        return staff_message

    def handle_batch_transition(self, transitions, submissions, **kwargs):
        kwargs.pop('submission')
        for submission in submissions:
            old_phase = transitions[submission.id]
            return self.handle_transition(old_phase=old_phase, submission=submission, **kwargs)

    def partners_updated(self, added, removed, **kwargs):
        message = ['Partners updated.']
        if added:
            message.append('Added:')
            message.append(', '.join([str(user) for user in added]) + '.')

        if removed:
            message.append('Removed:')
            message.append(', '.join([str(user) for user in removed]) + '.')

        return ' '.join(message)

    def send_message(self, message, user, submission, submissions, **kwargs):
        from .models import Activity, PUBLIC
        visibility = kwargs.get('visibility', PUBLIC)

        try:
            # If this was a batch action we want to pull out the submission
            submission = submissions[0]
        except IndexError:
            pass

        related = kwargs['related']
        if isinstance(related, dict):
            try:
                related = related[submission.id]
            except KeyError:
                pass

        has_correct_fields = all(hasattr(related, attr) for attr in ['author', 'submission', 'get_absolute_url'])
        if has_correct_fields and isinstance(related, models.Model):
            related_object = related
        else:
            related_object = None

        Activity.actions.create(
            user=user,
            submission=submission,
            timestamp=timezone.now(),
            message=message,
            visibility=visibility,
            related_object=related_object,
        )


class SlackAdapter(AdapterBase):
    adapter_type = "Slack"
    always_send = True
    messages = {
        MESSAGES.NEW_SUBMISSION: 'A new submission has been submitted for {submission.page.title}: <{link}|{submission.title}>',
        MESSAGES.UPDATE_LEAD: 'The lead of <{link}|{submission.title}> has been updated from {old_lead} to {submission.lead} by {user}',
        MESSAGES.BATCH_UPDATE_LEAD: 'handle_batch_lead',
        MESSAGES.COMMENT: 'A new {comment.visibility} comment has been posted on <{link}|{submission.title}> by {user}',
        MESSAGES.EDIT: '{user} has edited <{link}|{submission.title}>',
        MESSAGES.APPLICANT_EDIT: '{user} has edited <{link}|{submission.title}>',
        MESSAGES.REVIEWERS_UPDATED: 'reviewers_updated',
        MESSAGES.BATCH_REVIEWERS_UPDATED: 'handle_batch_reviewers',
        MESSAGES.PARTNERS_UPDATED: '{user} has updated the partners on <{link}|{submission.title}>',
        MESSAGES.TRANSITION: '{user} has updated the status of <{link}|{submission.title}>: {old_phase.display_name} → {submission.phase}',
        MESSAGES.BATCH_TRANSITION: 'handle_batch_transition',
        MESSAGES.DETERMINATION_OUTCOME: 'A determination for <{link}|{submission.title}> was sent by email. Outcome: {determination.clean_outcome}',
        MESSAGES.BATCH_DETERMINATION_OUTCOME: 'handle_batch_determination',
        MESSAGES.PROPOSAL_SUBMITTED: 'A proposal has been submitted for review: <{link}|{submission.title}>',
        MESSAGES.INVITED_TO_PROPOSAL: '<{link}|{submission.title}> by {submission.user} has been invited to submit a proposal',
        MESSAGES.NEW_REVIEW: '{user} has submitted a review for <{link}|{submission.title}>. Outcome: {review.outcome},  Score: {review.get_score_display}',
        MESSAGES.READY_FOR_REVIEW: 'notify_reviewers',
        MESSAGES.OPENED_SEALED: '{user} has opened the sealed submission: <{link}|{submission.title}>',
        MESSAGES.REVIEW_OPINION: '{user} {opinion.opinion_display}s with {opinion.review.author}''s review of {submission}',
        MESSAGES.BATCH_READY_FOR_REVIEW: 'batch_notify_reviewers',
        MESSAGES.DELETE_SUBMISSION: '{user} has deleted {submission.title}',
        MESSAGES.DELETE_REVIEW: '{user} has deleted {review.author} review for <{link}|{submission.title}>.',
        MESSAGES.CREATED_PROJECT: '{user} has created a Project: <{link}|{project.name}>.',
        MESSAGES.UPDATE_PROJECT_LEAD: 'The lead of project <{link}|{project.name}> has been updated from {old_lead} to {project.lead} by {user}',
        MESSAGES.EDIT_REVIEW: '{user} has edited {review.author} review for <{link}|{submission.title}>.',
    }

    def __init__(self):
        super().__init__()
        self.destination = settings.SLACK_DESTINATION_URL
        self.target_room = settings.SLACK_DESTINATION_ROOM

    def slack_links(self, links, submissions):
        return ', '.join(
            f'<{links[submission.id]}|{submission.title}>'
            for submission in submissions
        )

    def extra_kwargs(self, message_type, **kwargs):
        submission = kwargs['submission']
        submissions = kwargs['submissions']
        request = kwargs['request']
        link = link_to(submission, request)
        links = {
            submission.id: link_to(submission, request)
            for submission in submissions
        }
        return {
            'link': link,
            'links': links,
        }

    def recipients(self, message_type, submission, related, **kwargs):
        recipients = [self.slack_id(submission.lead)]

        # Notify second reviewer when first reviewer is done.
        if message_type == MESSAGES.NEW_REVIEW and related:
            if submission.assigned.with_roles().count() == 2 and related.author.reviewer == submission.assigned.with_roles().first().reviewer:
                recipients.append(self.slack_id(submission.assigned.with_roles().last().reviewer))

        return recipients

    def batch_recipients(self, message_type, submissions, **kwargs):
        # We group the messages by lead
        leads = User.objects.filter(id__in=submissions.values('lead'))
        return [
            {
                'recipients': [self.slack_id(lead)],
                'submissions': submissions.filter(lead=lead),
            } for lead in leads
        ]

    def reviewers_updated(self, submission, link, user, added=list(), removed=list(), **kwargs):
        message = [f'{user} has updated the reviewers on <{link}|{submission.title}>.']

        if added:
            message.append('Added:')
            message.extend(reviewers_message(added))

        if removed:
            message.append('Removed:')
            message.extend(reviewers_message(removed))

        return ' '.join(message)

    def handle_batch_lead(self, submissions, links, user, new_lead, **kwargs):
        submissions_text = self.slack_links(links, submissions)
        return (
            '{user} has batch changed lead to {new_lead} on: {submissions_text}'.format(
                user=user,
                submissions_text=submissions_text,
                new_lead=new_lead,
            )
        )

    def handle_batch_reviewers(self, submissions, links, user, added, **kwargs):
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

    def handle_batch_transition(self, user, links, submissions, transitions, **kwargs):
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

    def handle_batch_determination(self, submissions, links, determinations, **kwargs):
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

    def notify_reviewers(self, submission, link, **kwargs):
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

    def batch_notify_reviewers(self, submissions, links, **kwargs):
        kwargs.pop('submission')
        kwargs.pop('link')
        return '. '.join(
            self.notify_reviewers(submission, link=links[submission.id], **kwargs)
            for submission in submissions
        )

    def slack_id(self, user):
        if user.slack:
            return f'<{user.slack}>'
        return ''

    def slack_channels(self, submission):
        target_rooms = [self.target_room]
        try:
            extra_rooms = submission.get_from_parent('slack_channel').split(',')
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

    def send_message(self, message, recipient, submission, **kwargs):
        target_rooms = self.slack_channels(submission)

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
    }

    def get_subject(self, message_type, submission):
        if submission:
            if is_ready_for_review(message_type):
                subject = 'Application ready to review: {submission.title}'.format(submission=submission)
            else:
                subject = submission.page.specific.subject or 'Your application to Open Technology Fund: {submission.title}'.format(submission=submission)
            return subject

    def extra_kwargs(self, message_type, submission, submissions, **kwargs):
        return {
            'subject': self.get_subject(message_type, submission),
        }

    def handle_transition(self, old_phase, submission, **kwargs):
        # Retrive status index to see if we are going forward or backward.
        old_index = list(dict(PHASES).keys()).index(old_phase.name)
        target_index = list(dict(PHASES).keys()).index(submission.status)
        is_forward = old_index < target_index

        if is_forward:
            return self.render_message(
                'messages/email/transition.html',
                submission=submission,
                old_phase=old_phase,
                **kwargs
            )

    def handle_batch_transition(self, transitions, submissions, **kwargs):
        kwargs.pop('submission')
        for submission in submissions:
            old_phase = transitions[submission.id]
            return self.handle_transition(old_phase=old_phase, submission=submission, **kwargs)

    def batch_determination(self, determinations, submissions, **kwargs):
        kwargs.pop('submission')
        for submission in submissions:
            determination = determinations[submission.id]
            return self.render_message(
                'messages/email/determination.html',
                submission=submission,
                determination=determination,
                **kwargs
            )

    def notify_comment(self, **kwargs):
        comment = kwargs['comment']
        submission = kwargs['submission']
        if not comment.priviledged and not comment.user == submission.user:
            return self.render_message('messages/email/comment.html', **kwargs)

    def recipients(self, message_type, submission, **kwargs):
        if is_ready_for_review(message_type):
            return self.reviewers(submission)

        if is_transition(message_type):
            # Only notify the applicant if the new phase can be seen within the workflow
            if not submission.phase.permissions.can_view(submission.user):
                return []

        if message_type == MESSAGES.PARTNERS_UPDATED_PARTNER:
            partners = kwargs['added']
            return [partner.email for partner in partners]

        return [submission.user.email]

    def batch_recipients(self, message_type, submissions, **kwargs):
        if not is_ready_for_review(message_type):
            return super().batch_recipients(message_type, submissions, **kwargs)

        reviewers_to_message = defaultdict(list)
        for submission in submissions:
            reviewers = self.reviewers(submission)
            for reviewer in reviewers:
                reviewers_to_message[reviewer].append(submission)

        return [
            {
                'recipients': [reviewer],
                'submissions': submissions,
            } for reviewer, submissions in reviewers_to_message.items()
        ]

    def reviewers(self, submission):
        return [
            reviewer.email
            for reviewer in submission.missing_reviewers.all()
            if submission.phase.permissions.can_review(reviewer) and not reviewer.is_apply_staff
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

    def send_message(self, message, submission, subject, recipient, logs, **kwargs):
        try:
            send_mail(
                subject,
                message,
                submission.page.specific.from_address,
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
    }

    def batch_reviewers_updated(self, added, submissions, **kwargs):
        reviewers_text = ' '.join([
            f'{str(user)} as {role.name},'
            for role, user in added
            if user
        ])

        return (
            'Batch reviewers added: ' +
            reviewers_text +
            ' to ' +
            ', '.join(['"{}"'.format(submission.title) for submission in submissions])
        )

    def batch_transition(self, submissions, transitions, **kwargs):
        base_message = 'Successfully updated:'
        transition = '{submission} [{old_display} → {new_display}].'
        transition_messages = [
            transition.format(
                submission=submission.title,
                old_display=transitions[submission.id],
                new_display=submission.phase,
            ) for submission in submissions
        ]
        messages = [base_message, *transition_messages]
        return ' '.join(messages)

    def batch_determinations(self, submissions, determinations, **kwargs):
        outcome = determinations[submissions[0].id].clean_outcome

        base_message = f'Successfully determined as {outcome}: '
        submissions_text = [
            str(submission.title) for submission in submissions
        ]
        return base_message + ', '.join(submissions_text)

    def recipients(self, *args, **kwargs):
        return [None]

    def batch_recipients(self, message_type, submissions, *args, **kwargs):
        return [{
            'recipients': [None],
            'submissions': submissions,
        }]

    def send_message(self, message, request, **kwargs):
        messages.add_message(request, messages.INFO, message)


class MessengerBackend:
    def __init__(self, *adpaters):
        self.adapters = adpaters

    def __call__(self, *args, related=None, **kwargs):
        return self.send(*args, related=related, **kwargs)

    def send(self, message_type, request, user, related, submission=None, submissions=list(), **kwargs):
        from .models import Event
        if submission:
            event = Event.objects.create(type=message_type.name, by=user, submission=submission)
            for adapter in self.adapters:
                adapter.process(message_type, event, request=request, user=user, submission=submission, related=related, **kwargs)

        elif submissions:
            events = Event.objects.bulk_create(
                Event(type=message_type.name, by=user, submission=submission)
                for submission in submissions
            )
            for adapter in self.adapters:
                adapter.process_batch(message_type, events, request=request, user=user, submissions=submissions, related=related, **kwargs)


adapters = [
    ActivityAdapter(),
    SlackAdapter(),
    EmailAdapter(),
    DjangoMessagesAdapter(),
]


messenger = MessengerBackend(*adapters)
