import json
import requests
from collections import defaultdict

from django.db import models
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string

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
    MESSAGES.UPDATE_LEAD: 'old_lead',
    MESSAGES.NEW_REVIEW: 'review',
    MESSAGES.TRANSITION: 'old_phase',
    MESSAGES.BATCH_TRANSITION: 'transitions',
    MESSAGES.APPLICANT_EDIT: 'revision',
    MESSAGES.EDIT: 'revision',
    MESSAGES.COMMENT: 'comment',
    MESSAGES.SCREENING: 'old_status',
}


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
        recipients = self.recipients(message_type, submission=submission, **kwargs)
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
                    message = '{} [to: {}]: {}'.format(self.adapter_type, recipient, message)
                else:
                    message = '{}: {}'.format(self.adapter_type, message)
                messages.add_message(request, messages.DEBUG, message)

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
        MESSAGES.DETERMINATION_OUTCOME: 'Sent a determination. Outcome: {determination.clean_outcome}',
        MESSAGES.INVITED_TO_PROPOSAL: 'Invited to submit a proposal',
        MESSAGES.REVIEWERS_UPDATED: 'reviewers_updated',
        MESSAGES.BATCH_REVIEWERS_UPDATED: 'batch_reviewers_updated',
        MESSAGES.NEW_REVIEW: 'Submitted a review',
        MESSAGES.OPENED_SEALED: 'Opened the submission while still sealed',
        MESSAGES.SCREENING: 'Screening status from {old_status} to {submission.screening_status}'
    }

    def recipients(self, message_type, **kwargs):
        return [None]

    def extra_kwargs(self, message_type, submission, submissions, **kwargs):
        from .models import INTERNAL
        if message_type in [MESSAGES.OPENED_SEALED, MESSAGES.REVIEWERS_UPDATED, MESSAGES.SCREENING]:
            return {'visibility': INTERNAL}
        is_transition = message_type in [MESSAGES.TRANSITION, MESSAGES.BATCH_TRANSITION]

        submission = submission or submissions[0]
        if is_transition and not submission.phase.permissions.can_view(submission.user):
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
        return 'Batch ' + self.reviewers_updated(added, **kwargs)

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
            old_phase = transitions[submission.phase]
            return self.handle_transition(old_phase=old_phase, submission=submission, **kwargs)

    def send_message(self, message, user, submission, submissions, **kwargs):
        from .models import Activity, PUBLIC
        visibility = kwargs.get('visibility', PUBLIC)

        related = kwargs['related']
        has_correct_fields = all(hasattr(related, attr) for attr in ['author', 'submission', 'get_absolute_url'])
        if has_correct_fields and isinstance(related, models.Model):
            related_object = related
        else:
            related_object = None

        try:
            # If this was a batch action we want to pull out the submission
            submission = submissions[0]
        except IndexError:
            pass

        Activity.actions.create(
            user=user,
            submission=submission,
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
        MESSAGES.COMMENT: 'A new {comment.visibility} comment has been posted on <{link}|{submission.title}> by {user}',
        MESSAGES.EDIT: '{user} has edited <{link}|{submission.title}>',
        MESSAGES.APPLICANT_EDIT: '{user} has edited <{link}|{submission.title}>',
        MESSAGES.REVIEWERS_UPDATED: 'reviewers_updated',
        MESSAGES.BATCH_REVIEWERS_UPDATED: 'handle_batch_reviewers',
        MESSAGES.TRANSITION: '{user} has updated the status of <{link}|{submission.title}>: {old_phase.display_name} → {submission.phase}',
        MESSAGES.BATCH_TRANSITION: 'handle_batch_transition',
        MESSAGES.DETERMINATION_OUTCOME: 'A determination for <{link}|{submission.title}> was sent by email. Outcome: {determination.clean_outcome}',
        MESSAGES.PROPOSAL_SUBMITTED: 'A proposal has been submitted for review: <{link}|{submission.title}>',
        MESSAGES.INVITED_TO_PROPOSAL: '<{link}|{submission.title}> by {submission.user} has been invited to submit a proposal',
        MESSAGES.NEW_REVIEW: '{user} has submitted a review for <{link}|{submission.title}>. Outcome: {review.outcome},  Score: {review.score}',
        MESSAGES.READY_FOR_REVIEW: 'notify_reviewers',
        MESSAGES.OPENED_SEALED: '{user} has opened the sealed submission: <{link}|{submission.title}>'
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

    def recipients(self, message_type, submission, **kwargs):
        return [self.slack_id(submission.lead)]

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

    def handle_batch_reviewers(self, submissions, links, user, added, **kwargs):
        submissions_text = self.slack_links(links, submissions)
        reviewers_text = ', '.join([str(user) for user in added])
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
                f'{transitions[submission.phase].display_name} → {submission.phase}',
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

    def notify_reviewers(self, submission, **kwargs):
        reviewers_to_notify = []
        for reviewer in submission.reviewers.all():
            if submission.phase.permissions.can_review(reviewer):
                reviewers_to_notify.append(reviewer)

        reviewers = ', '.join(
            self.slack_id(reviewer) or str(reviewer) for reviewer in reviewers_to_notify
        )

        return (
            '<{link}|{submission.title}> is ready for review. The following are assigned as reviewers: {reviewers}'.format(
                reviewers=reviewers,
                submission=submission,
                **kwargs
            )
        )

    def slack_id(self, user):
        if user.slack:
            return f'<{user.slack}>'
        return ''

    def slack_channel(self, submission):
        try:
            target_room = submission.get_from_parent('slack_channel')
        except AttributeError:
            # If not a submission object, set room to default.
            target_room = self.target_room
        else:
            if not target_room:
                # If no custom room, set to default.
                target_room = self.target_room

        # Make sure the channel name starts with a "#".
        if target_room and not target_room.startswith('#'):
            target_room = f"#{target_room}"

        return target_room

    def send_message(self, message, recipient, **kwargs):
        try:
            submission = kwargs['submission']
        except Exception:
            # If no submission, set room to default.
            target_room = self.target_room
        else:
            target_room = self.slack_channel(submission)

        if not self.destination or not target_room:
            errors = list()
            if not self.destination:
                errors.append('Destination URL')
            if not target_room:
                errors.append('Room ID')
            return 'Missing configuration: {}'.format(', '.join(errors))

        message = ' '.join([recipient, message]).strip()

        data = {
            "room": target_room,
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
        MESSAGES.TRANSITION: 'messages/email/transition.html',
        MESSAGES.BATCH_TRANSITION: 'handle_batch_transition',
        MESSAGES.DETERMINATION_OUTCOME: 'messages/email/determination.html',
        MESSAGES.INVITED_TO_PROPOSAL: 'messages/email/invited_to_proposal.html',
        MESSAGES.READY_FOR_REVIEW: 'messages/email/ready_to_review.html',
    }

    def get_subject(self, message_type, submission):
        if submission:
            if message_type == MESSAGES.READY_FOR_REVIEW:
                subject = 'Application ready to review: {submission.title}'.format(submission=submission)
            else:
                subject = submission.page.specific.subject or 'Your application to Open Technology Fund: {submission.title}'.format(submission=submission)
            return subject

    def extra_kwargs(self, message_type, submission, submissions, **kwargs):
        return {
            'subject': self.get_subject(message_type, submission),
        }

    def handle_batch_transition(self, transitions, submissions, **kwargs):
        kwargs.pop('submission')
        for submission in submissions:
            old_phase = transitions[submission.phase]
            return self.render_message(
                'messages/email/transition.html',
                submission=submission,
                old_phase=old_phase,
                **kwargs
            )

    def notify_comment(self, **kwargs):
        comment = kwargs['comment']
        submission = kwargs['submission']
        if not comment.priviledged and not comment.user == submission.user:
            return self.render_message('messages/email/comment.html', **kwargs)

    def recipients(self, message_type, submission, **kwargs):
        if message_type == MESSAGES.READY_FOR_REVIEW:
            return self.reviewers(submission)

        if message_type in [MESSAGES.TRANSITION, MESSAGES.BATCH_TRANSITION]:
            # Only notify the applicant if the new phase can be seen within the workflow
            if not submission.phase.permissions.can_view(submission.user):
                return []
        return [submission.user.email]

    def reviewers(self, submission):
        return [
            reviewer.email
            for reviewer in submission.missing_reviewers.all()
            if submission.phase.permissions.can_review(reviewer)
        ]

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
    }

    def batch_reviewers_updated(self, added, submissions, **kwargs):
        return (
            'Batch reviewers added: ' +
            ', '.join([str(user) for user in added]) +
            ' to ' +
            ', '.join(['"{}"'.format(submission.title) for submission in submissions])
        )

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
