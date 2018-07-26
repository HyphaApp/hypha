from enum import Enum

import requests

from django.conf import settings
from django.contrib import messages

from .models import Activity


class MESSAGES(Enum):
    UPDATE_LEAD = 'update_lead'
    NEW_SUBMISSION = 'new_submission'
    TRANSITION = 'transition'
    NEW_DETERMINATION = 'new_determination'
    DETERMINATION_OUTCOME = 'determination_outcome'
    INVITED_TO_PROPOSAL = 'invited_to_proposal'
    REVIEWERS_UPDATED = 'reviewers_updated'
    NEW_REVIEW = 'new_review'
    COMMENT = 'comment'


class AdapterBase:
    messages = {}
    always_send = False

    def message(self, message_type, **kwargs):
        message = self.messages[message_type]
        try:
            # see if its a method on the adapter
            method = getattr(self, message)
        except AttributeError:
            return message.format(**kwargs)
        else:
            return method(**kwargs)

    def process(self, message_type, **kwargs):
        try:
            message = self.message(message_type, **kwargs)
        except KeyError:
            return
        if settings.SEND_MESSAGES or self.always_send:
            self.send_message(message, **kwargs)

        if not settings.SEND_MESSAGES:
            message  = self.adapter_type + ': ' + message
            messages.add_message(kwargs['request'], messages.INFO, message)


    def send_message(self, message, **kwargs):
        raise NotImplementedError()


class ActivityAdapter(AdapterBase):
    adapter_type = "Activity Feed"
    always_send = True
    messages = {
        MESSAGES.TRANSITION: 'Progressed from {old_phase.display_name} to {submission.phase}',
        MESSAGES.NEW_SUBMISSION: 'Submitted {submission.title} for {submission.page.title}',
        MESSAGES.UPDATE_LEAD: 'Lead changed from {old.lead} to {submission.lead}',
        MESSAGES.NEW_DETERMINATION: 'Created a determination for {submission.title}',
        MESSAGES.DETERMINATION_OUTCOME: 'Sent a {submission.determination.get_outcome_display} determination for {submission.title}:\r\n{determination.clean_message}',
        MESSAGES.INVITED_TO_PROPOSAL: '{submission.title} has been invited to submit a proposal.',
        MESSAGES.REVIEWERS_UPDATED: 'reviewers_updated',
        MESSAGES.NEW_REVIEW: 'Created a review for {submission.title}'
    }

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
        Activity.actions.create(
            user=user,
            submission=submission,
            message=message,
        )


class SlackAdapter(AdapterBase):
    adapter_type = "Slack"
    always_send = True
    messages = {
        MESSAGES.UPDATE_LEAD: 'The lead of "{submission.title}" has been updated form { old.lead } to {submission.lead} by {user}',
        MESSAGES.COMMENT: 'A new comment has been posted on "{submission.title}"',
    }

    def __init__(self):
        super().__init__()
        self.destination = settings.SLACK_DESTINATION

    def message(self, message_type,  **kwargs):
        message = super().message(message_type, **kwargs)
        user = kwargs['user']
        submission = kwargs['submission']
        message = ' '.join([self.slack_id(submission.lead), message])
        return message

    def slack_id(self, user):
        if user.slack:
            return f'<{user.slack}>'
        else:
            return str(user)

    def send_message(self, message, **kwargs):
        if not self.destination:
            return

        data = {
            "room": "CBQUCH458",
            "message": message,
        }
        requests.post(self.destination, data=data)


class MessengerBackend:
    def __init__(self, *adpaters):
        self.adapters = adpaters

    def __call__(self, message_type, request, user, submission, **kwargs):
        return self.send(message_type, request=request, user=user, submission=submission, **kwargs)

    def send(self, message_type, **kwargs):
        for adapter in self.adapters:
            adapter.process(message_type, **kwargs)


adapters = [
    ActivityAdapter(),
    SlackAdapter(),
]


messenger = MessengerBackend(*adapters)
