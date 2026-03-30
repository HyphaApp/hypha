from django.conf import settings
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.utils import formats, timezone
from django.utils.translation import gettext_lazy as _
from wagtail.models import Site

from hypha.core.mail import MarkdownMail


@receiver(user_logged_in)
def send_login_notification(sender, request, user, **kwargs):
    if not settings.SEND_MESSAGES or not user.email:
        return

    email = MarkdownMail("users/emails/login_notification.md")
    email.send(
        to=user.email,
        subject=_("Successful login to %(org)s") % {"org": settings.ORG_LONG_NAME},
        from_email=settings.DEFAULT_FROM_EMAIL,
        context={
            "user": user,
            "login_time": formats.date_format(timezone.now(), "SHORT_DATETIME_FORMAT"),
            "site": Site.find_for_request(request) if request else None,
            "ORG_EMAIL": settings.ORG_EMAIL,
        },
    )
