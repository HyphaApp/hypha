from enum import Enum

import requests

from django.conf import settings
from django.contrib import messages

from .models import Activity


def link_to(target, request):
    return request.scheme + '://' + request.get_host() + target.get_absolute_url()


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
    PROPOSAL_SUBMITTED = 'proposal_submitted'


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
        message = self.message(message_type, **kwargs)

        if not message:
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
        MESSAGES.NEW_SUBMISSION: 'A new submission has been submitted for {{submission.page.title}}: <{link}|{submission.title}>',
        MESSAGES.UPDATE_LEAD: 'The lead of <{link}|{submission.title}> has been updated from {old.lead} to {submission.lead} by {user}',
        MESSAGES.COMMENT: 'A new comment has been posted on <{link}|{submission.title}>',
        MESSAGES.REVIEWERS_UPDATED: '{user} has updated the reviewers on <{link}|{submission.title}>',
        MESSAGES.TRANSITION: '{user} has updated the status of <{link}|{submission.title}>: {old_phase.display_name} → {submission.phase}',
        MESSAGES.DETERMINATION_OUTCOME: 'A determination for <{link}|{submission.title}> was sent by email: {submission.determination.get_outcome_display}',
        MESSAGES.PROPOSAL_SUBMITTED: 'A proposal has been submitted for review: <{link}|{submission.title}>',
    }

    def __init__(self):
        super().__init__()
        self.destination = settings.SLACK_DESTINATION

    def message(self, message_type,  **kwargs):
        user = kwargs['user']
        submission = kwargs['submission']
        request = kwargs['request']
        link = link_to(submission, request)

        message = super().message(message_type, link=link, **kwargs)

        if submission.lead.slack:
            slack_target = self.slack_id(submission.lead)
        else:
            slack_target = ''

        message = ' '.join([slack_target, message]).strip()
        return message

    def slack_id(self, user):
        return f'<{user.slack}>'

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
