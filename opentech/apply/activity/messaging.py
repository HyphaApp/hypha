from enum import Enum
from django.contrib import messages

from .models import Activity


class MESSAGES(Enum):
    UPDATE_LEAD = 'update_lead'

class MessageAdapter:
    def process(self, request, payload):
        messages.add_message(request, messages.INFO, 'Hello world.')


class ActivityAdapter:
    messages = {
        MESSAGES.UPDATE_LEAD: 'Lead changed from {old.lead} to {new.lead}',
    }

    def message(self, message_type):
        return self.messages[message_type]

    def process(self, message_type, **kwargs):
        try:
            message = self.message(message_type)
        except KeyError:
            return

        Activity.actions.create(
            user=kwargs['user'],
            submission=kwargs['submission'],
            message=message.format(**kwargs),
        )


class MessengerBackend:
    adapters = [ActivityAdapter()]

    def __call__(self, message_type, user, submission, **kwargs):
        return self.send(message_type, user=user, submission=submission, **kwargs)

    def send(self, message_type, **kwargs):
        for adapter in self.adapters:
            adapter.process(message_type, **kwargs)


messenger = MessengerBackend()
