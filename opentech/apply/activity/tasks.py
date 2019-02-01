from celery import Celery

from django.conf import settings
from django.core.mail import EmailMessage

app = Celery('tasks')

app.config_from_object(settings, namespace='CELERY', force=True)


def send_mail(subject, message, from_address, recipients, logs=None):
    # Convenience method to wrap the tasks and handle the callback
    send_mail_task.apply_async(
        kwargs={
            'subject': subject,
            'body': message,
            'from_email': from_address,
            'to': recipients,
        },
        link=update_message_status.s(log.values_list('id', flat=True)),
    )


@app.task
def send_mail_task(**kwargs):
    response = {'status': '', 'id': None}
    email = EmailMessage(**kwargs)
    try:
        email.send()
    except Exception as e:
        response['status'] = 'Error: ' + str(e)
    else:
        try:
            return {
                'status': email.anymail_status.status.pop(),
                'id': email.anymail_status.message_id,
            }
        except AttributeError:
            response['status'] = 'sent'

    return response


@app.task
def update_message_status(response, message_ids):
    from .models import Message
    message = Message.objects.filter(id__in=message_ids)
    message.external_id = response['id']
    message.update_status(response['status'])
