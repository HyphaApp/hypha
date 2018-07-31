from celery import Celery

from django.conf import settings
from django.core.mail import send_mail as dj_send_mail

app = Celery('tasks')

app.config_from_object(settings, namespace='CELERY', force=True)


@app.task
def send_mail(*args, **kwargs):
    try:
        emails_sent = dj_send_mail(
            *args,
            fail_silently=False,
            **kwargs,
        )
    except Exception as e:
        return 'Error: ' + str(e)

    return 'Emails sent: ' + str(emails_sent)


@app.task
def update_message_status(status, message):
    from .models import Message
    Message.objects.get(id=message).update_status(status)
