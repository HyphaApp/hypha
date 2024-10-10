from django.conf import settings
from django.dispatch import receiver
from django.utils.html import strip_tags

from hypha.apply.activity.adapters.emails import EmailAdapter
from hypha.apply.activity.adapters.slack import SlackAdapter
from hypha.apply.activity.signals import message_hook
from hypha.home.models import ApplyHomePage

from .models import MessagingSetting, MessagingSettings


def replace_settings_message_keywords(message, **kwargs):
    # Because this is working in tandem with a templating system that is very forgiving of
    # things being the wrong type or absent, the method we use for these replacements is
    # to attempt to add them, and just not add each replacement if the information is
    # not in kwargs or is wrong.
    request = kwargs.get("request")
    source = kwargs.get("source")
    submission = kwargs.get("submission")
    invoice = kwargs.get("invoice")
    user = kwargs.get("user")
    determination = kwargs.get("determination")

    replacements = []

    # Submission from source based replacements
    try:
        replacements.extend(
            [
                (
                    "SUBMISSION_URL",
                    "%s://%s%s"
                    % (request.scheme, request.get_host(), source.get_absolute_url()),
                ),
                ("SUBMISSION_FUND_TITLE", source.page.title),
                ("SUBMISSION_TITLE", source.title),
                ("SUBMISSION_USER_NAME", source.user.get_full_name()),
                ("SUBMISSION_USER_EMAIL", source.user.email),
                (
                    "SUBMISSION_CONFIRMATION_TEXT_EXTRA",
                    source.page.specific.confirmation_text_extra,
                ),
            ]
        )
    except AttributeError:
        pass

    # Submission from submission based replacements
    try:
        replacements.extend(
            [
                (
                    "SUBMISSION_URL",
                    "%s://%s%s"
                    % (
                        request.scheme,
                        request.get_host(),
                        submission.get_absolute_url(),
                    ),
                ),
                ("SUBMISSION_FUND_TITLE", submission.page.title),
                ("SUBMISSION_TITLE", submission.title),
                ("SUBMISSION_USER_NAME", submission.user.get_full_name()),
                ("SUBMISSION_USER_EMAIL", submission.user.email),
                (
                    "SUBMISSION_CONFIRMATION_TEXT_EXTRA",
                    submission.page.specific.confirmation_text_extra,
                ),
            ]
        )
    except AttributeError:
        pass

    # Determination based replacements
    try:
        replacements.extend(
            [
                (
                    "DETERMINATION_URL",
                    "%s://%s%s"
                    % (
                        request.scheme,
                        request.get_host(),
                        determination.get_absolute_url(),
                    ),
                ),
                ("DETERMINATION_MESSAGE", strip_tags(determination.message)),
                ("DETERMINATION_OUTCOME", determination.clean_outcome),
            ]
        )
    except AttributeError:
        pass

    # Project based replacements
    try:
        replacements.extend(
            [
                ("PROJECT_TITLE", source.title),
                (
                    "PROJECT_URL",
                    "%s://%s%s"
                    % (request.scheme, request.get_host(), source.get_absolute_url()),
                ),
                (
                    "SUBMISSION_URL",
                    "%s://%s%s"
                    % (
                        request.scheme,
                        request.get_host(),
                        source.submission.get_absolute_url(),
                    ),
                ),
                ("PROJECT_LEAD_EMAIL", source.lead.email),
                ("PROJECT_LEAD_NAME", source.lead.get_full_name()),
            ]
        )
    except AttributeError:
        pass

    # Invoice based replacements
    try:
        replacements.extend(
            [
                (
                    "INVOICE_URL",
                    "%s://%s%s"
                    % (request.scheme, request.get_host(), invoice.get_absolute_url()),
                ),
            ]
        )
    except AttributeError:
        pass

    try:
        replacements.extend(
            [
                ("ORG_EMAIL", settings.ORG_EMAIL),
                ("ORG_SHORT_NAME", settings.ORG_SHORT_NAME),
                ("ORG_LONG_NAME", settings.ORG_LONG_NAME),
                ("ORG_URL", settings.ORG_URL),
                ("ORG_GUIDE_URL", settings.ORG_GUIDE_URL),
            ]
        )
    except AttributeError:
        pass

    try:
        replacements.append(("USER_NAME", str(user)))
    except AttributeError:
        pass

    for old, new in replacements:
        if new:
            message = message.replace(old, new)

    return message


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
        response["message"] = replace_settings_message_keywords(message, **kwargs)

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
        response["message"] = replace_settings_message_keywords(
            messaging_setting_for_type.slack_message or "", **kwargs
        )
    except MessagingSettings.DoesNotExist:
        pass

    return response
