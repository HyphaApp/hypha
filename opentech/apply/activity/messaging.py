from enum import Enum

import requests

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string


def link_to(target, request):
    return request.scheme + '://' + request.get_host() + target.get_absolute_url()


class MESSAGES(Enum):
    UPDATE_LEAD = 'Update Lead'
    NEW_SUBMISSION = 'New Submission'
    TRANSITION = 'Transition'
    DETERMINATION_OUTCOME = 'Determination Outcome'
    INVITED_TO_PROPOSAL = 'Invited To Proposal'
    REVIEWERS_UPDATED = 'Reviewers Updated'
    READY_FOR_REVIEW = 'Ready For Review'
    NEW_REVIEW = 'New Review'
    COMMENT = 'Comment'
    PROPOSAL_SUBMITTED = 'Proposal Submitted'

    @classmethod
    def choices(cls):
        return [
            (choice.name, choice.value)
            for choice in cls
        ]


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

    def recipients(self, message_type, **kwargs):
        raise NotImplementedError()

    def process(self, message_type, event, **kwargs):
        kwargs.update(self.extra_kwargs(message_type, **kwargs))

        message = self.message(message_type, **kwargs)
        if not message:
            return

        for recipient in self.recipients(message_type, **kwargs):
            if settings.SEND_MESSAGES or self.always_send:
                status = self.send_message(message, recipient=recipient, **kwargs)
            else:
                status = 'Message not sent as SEND_MESSAGES==FALSE'

            if status:
                self.log_message(message, recipient, event, status)

            if not settings.SEND_MESSAGES:
                if recipient:
                    message = '{} [to: {}]: {}'.format(self.adapter_type, recipient, message)
                else:
                    message = '{}: {}'.format(self.adapter_type, message)
                messages.add_message(kwargs['request'], messages.INFO, message)

    def log_message(self, message, recipient, event, status):
        from.models import Message
        Message.objects.create(
            type=self.adapter_type,
            content=message,
            recipient=recipient,
            event=event,
            status=status,
        )

    def send_message(self, message, **kwargs):
        # Process the message, should return the result of the send
        # Returning None will not record this action
        raise NotImplementedError()


class ActivityAdapter(AdapterBase):
    adapter_type = "Activity Feed"
    always_send = True
    messages = {
        MESSAGES.TRANSITION: 'Progressed from {old_phase.display_name} to {submission.phase}',
        MESSAGES.NEW_SUBMISSION: 'Submitted {submission.title} for {submission.page.title}',
        MESSAGES.UPDATE_LEAD: 'Lead changed from {old.lead} to {submission.lead}',
        MESSAGES.DETERMINATION_OUTCOME: 'Sent a determination. Outcome: {submission.determination.clean_outcome}',
        MESSAGES.INVITED_TO_PROPOSAL: 'Invited to submit a proposal',
        MESSAGES.REVIEWERS_UPDATED: 'reviewers_updated',
        MESSAGES.NEW_REVIEW: '{user} submitted a review'
    }

    def recipients(self, message_type, **kwargs):
        return [None]

    def reviewers_updated(self, added, removed, **kwargs):
        message = ['Reviewers updated.']
        if added:
            message.append('Added:')
            message.append(', '.join([str(user) for user in added]) + '.')

        if removed:
            message.append('Removed:')
            message.append(', '.join([str(user) for user in removed]) + '.')

        return ' '.join(message)

    def send_message(self, message, user, submission, **kwargs):
        from .models import Activity
        Activity.actions.create(
            user=user,
            submission=submission,
            message=message,
        )


class SlackAdapter(AdapterBase):
    adapter_type = "Slack"
    always_send = True
    messages = {
        MESSAGES.NEW_SUBMISSION: 'A new submission has been submitted for {submission.page.title}: <{link}|{submission.title}>',
        MESSAGES.UPDATE_LEAD: 'The lead of <{link}|{submission.title}> has been updated from {old.lead} to {submission.lead} by {user}',
        MESSAGES.COMMENT: 'A new comment has been posted on <{link}|{submission.title}>',
        MESSAGES.REVIEWERS_UPDATED: '{user} has updated the reviewers on <{link}|{submission.title}>',
        MESSAGES.TRANSITION: '{user} has updated the status of <{link}|{submission.title}>: {old_phase.display_name} → {submission.phase}',
        MESSAGES.DETERMINATION_OUTCOME: 'A determination for <{link}|{submission.title}> was sent by email. Outcome: {submission.determination.clean_outcome}',
        MESSAGES.PROPOSAL_SUBMITTED: 'A proposal has been submitted for review: <{link}|{submission.title}>',
        MESSAGES.INVITED_TO_PROPOSAL: '<{link}|{submission.title}> by {submission.user} has been invited to submit a proposal',
        MESSAGES.NEW_REVIEW: '{user} has submitted a review for <{link}|{submission.title}>. Outcome: {review.outcome} Score: {review.score}',
        MESSAGES.READY_FOR_REVIEW: 'notify_reviewers',
    }

    def __init__(self):
        super().__init__()
        self.destination = settings.SLACK_DESTINATION_URL
        self.target_room = settings.SLACK_DESTINATION_ROOM

    def extra_kwargs(self, message_type, **kwargs):
        submission = kwargs['submission']
        request = kwargs['request']
        link = link_to(submission, request)
        return {'link': link}

    def recipients(self, message_type, submission, **kwargs):
        return [self.slack_id(submission.lead)]

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

    def send_message(self, message, recipient, **kwargs):
        if not self.destination or not self.target_room:
            errors = list()
            if not self.destination:
                errors.append('Destination URL')
            if not self.target_room:
                errors.append('Room ID')
            return 'Missing configuration: {}'.format(', '.join(errors))

        message = ' '.join([recipient, message]).strip()

        data = {
            "room": self.target_room,
            "message": message,
        }
        return requests.post(self.destination, json=data)


class EmailAdapter(AdapterBase):
    adapter_type = 'Email'
    messages = {
        MESSAGES.NEW_SUBMISSION: 'funds/email/confirmation.html',
        MESSAGES.COMMENT: 'notify_comment',
        MESSAGES.TRANSITION: 'messages/email/transition.html',
        MESSAGES.DETERMINATION_OUTCOME: 'messages/email/determination.html',
        MESSAGES.INVITED_TO_PROPOSAL: 'messages/email/invited_to_proposal.html',
        MESSAGES.READY_FOR_REVIEW: 'messages/email/ready_to_review.html',
    }

    def extra_kwargs(self, message_type, submission, **kwargs):
        if message_type == MESSAGES.READY_FOR_REVIEW:
            subject = 'Application ready to review: {submission.title}'.format(submission=submission)
        else:
            subject = submission.page.specific.subject or 'Your application to Open Technology Fund: {submission.title}'.format(submission=submission)
        return {
            'subject': subject,
        }

    def notify_comment(self, **kwargs):
        comment = kwargs['comment']
        submission = kwargs['submission']
        if not comment.private and not comment.user == submission.user:
            return self.render_message('messages/email/comment.html', **kwargs)

    def recipients(self, message_type, submission, **kwargs):
        if message_type == MESSAGES.READY_FOR_REVIEW:
            return self.reviewers(submission)
        return [submission.user.email]

    def reviewers(self, submission):
        return [
            reviewer.email
            for reviewer in submission.reviewers.all()
            if submission.phase.permissions.can_review(reviewer)
        ]

    def render_message(self, template, **kwargs):
        return render_to_string(template, kwargs)

    def send_message(self, message, submission, subject, recipient, **kwargs):
        return send_mail(
            subject,
            message,
            submission.page.specific.from_address,
            [recipient],
        )


class MessengerBackend:
    def __init__(self, *adpaters):
        self.adapters = adpaters

    def __call__(self, message_type, request, user, submission, **kwargs):
        return self.send(message_type, request=request, user=user, submission=submission, **kwargs)

    def send(self, message_type, user, submission, **kwargs):
        from.models import Event
        event = Event.objects.create(type=message_type.name, by=user, submission=submission)
        for adapter in self.adapters:
            adapter.process(message_type, event, user=user, submission=submission, **kwargs)


adapters = [
    ActivityAdapter(),
    SlackAdapter(),
    EmailAdapter(),
]


messenger = MessengerBackend(*adapters)
