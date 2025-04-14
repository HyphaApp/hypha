from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMessage


def send_mail(subject, message, from_address, recipients, logs=None):
    if settings.EMAIL_SUBJECT_PREFIX:
        subject = str(settings.EMAIL_SUBJECT_PREFIX) + str(subject)
    # Convenience method to wrap the tasks and handle the callback
    print("PRE-TASK")
    task = send_mail_task.apply_async(
        kwargs={
            "subject": subject,
            "body": message,
            "from_email": from_address,
            "to": recipients,
        },
        link=update_message_status.s([log.pk for log in logs]),
    )
    print("TASK")
    print(task)
    print(task.result())


@shared_task
def send_mail_task(**kwargs):
    print("MAIL TASK")
    response = {"status": "", "id": None}
    email = EmailMessage(**kwargs)
    try:
        email.send()
    except Exception as e:
        response["status"] = "Error: " + str(e)
    else:
        try:
            return {
                "status": email.anymail_status.status.pop(),
                "id": email.anymail_status.message_id,
            }
        except AttributeError:
            response["status"] = "sent"

    return response


@shared_task
def update_message_status(response, message_pks):
    from .models import Message

    print("UPDATE STATUS")

    messages = Message.objects.filter(pk__in=message_pks)
    messages.update(external_id=response["id"])
    messages.update_status(response["status"])
