from anymail.signals import tracking
from django.dispatch import receiver

from .models import Message


@receiver(tracking)
def handle_event(sender, event, esp_name, **kwargs):
    status = 'Webhook received: {} [{}]'.format(event.event_type, event.timestamp)
    if event.description:
        status += ' ' + event.description
    Message.objects.get(external_id=event.message_id).update_status(status)
