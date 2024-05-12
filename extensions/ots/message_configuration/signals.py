from django.dispatch import receiver

from hypha.apply.activity.adapters.emails import EmailAdapter
from hypha.apply.activity.adapters.slack import SlackAdapter
from hypha.apply.activity.signals import message_hook
from hypha.home.models import ApplyHomePage

from .models import MessagingSetting, MessagingSettings


@receiver(message_hook, sender=EmailAdapter)
def handle_email_message_hook(sender, message_type, **kwargs):
    site = ApplyHomePage.objects.first().get_site()
    messaging_setting = MessagingSetting.objects.filter(site=site).first()

    if not messaging_setting:
        return {}

    response = {"should_send": messaging_setting.email_default_send}

    try:
        messaging_setting_for_type = messaging_setting.messaging_settings.get(
            message_type=message_type
        )

        response["extra_kwargs"] = {"subject": messaging_setting_for_type.email_subject}
        response["should_send"] = messaging_setting_for_type.email_enabled

        message = ""

        if messaging_setting_for_type.email_message:
            header = messaging_setting.email_header
            footer = messaging_setting.email_footer

            if header:
                message = message + header + "\n"
            message = message + messaging_setting_for_type.email_message
            if footer:
                message = message + "\n" + footer + "\n"
        response["message"] = message

    except MessagingSettings.DoesNotExist:
        pass

    return response


@receiver(message_hook, sender=SlackAdapter)
def handle_slack_message_hook(sender, message_type, **kwargs):
    site = ApplyHomePage.objects.first().get_site()
    messaging_setting = MessagingSetting.objects.filter(site=site).first()

    if not messaging_setting:
        return {}

    response = {"should_send": messaging_setting.slack_default_send}

    try:
        messaging_setting_for_type = messaging_setting.messaging_settings.get(
            message_type=message_type
        )

        response["should_send"] = messaging_setting_for_type.slack_enabled
        response["message"] = messaging_setting_for_type.slack_message
    except MessagingSettings.DoesNotExist:
        pass

    return response
