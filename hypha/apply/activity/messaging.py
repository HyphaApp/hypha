import logging

from django.contrib.auth import get_user_model

from .adapters import ActivityAdapter, DjangoMessagesAdapter, EmailAdapter, SlackAdapter

logger = logging.getLogger(__name__)
User = get_user_model()

from .options import MESSAGES  # noqa


class MessengerBackend:
    def __init__(self, *adapters):
        self.adapters = adapters

    def __call__(self, *args, related=None, **kwargs):
        return self.send(*args, related=related, **kwargs)

    def send(
        self, message_type, request, user, related, source=None, sources=None, **kwargs
    ):
        from .models import Event

        print("SEND CALL")
        print("MESSAGE TYPE:")
        print(message_type)
        print("REQUEST:")
        print(request)
        print("USER:")
        print(user)
        print("RELATED:")
        print(related)
        print("SOURCE:")
        print(source)
        print("SOURCES:")
        print(sources)
        print()

        if sources is None:
            sources = []

        if source:
            event = Event.objects.create(type=message_type.name, by=user, source=source)
            for adapter in self.adapters:
                adapter.process(
                    message_type,
                    event,
                    request=request,
                    user=user,
                    source=source,
                    related=related,
                    **kwargs,
                )

        elif sources:
            events = Event.objects.bulk_create(
                Event(type=message_type.name, by=user, source=source)
                for source in sources
            )
            for adapter in self.adapters:
                adapter.process_batch(
                    message_type,
                    events,
                    request=request,
                    user=user,
                    sources=sources,
                    related=related,
                    **kwargs,
                )


adapters = [
    ActivityAdapter(),
    SlackAdapter(),
    EmailAdapter(),
    DjangoMessagesAdapter(),
]

messenger = MessengerBackend(*adapters)
