from django.db import models
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.models import Orderable

from hypha.apply.activity.options import MESSAGES


@register_setting
class MessagingSetting(BaseSiteSetting, ClusterableModel):
    """Allows settings per Message Type to be specified in Wagtail Settings and retrieved by the activity code.
    This class affords a setting for a single Site to be referenced by the MessagingSettings model. This way
    the BaseSiteSetting can be extended such that a setting appears in the Wagtail Settings menu but there can also be up to
    one row per group for settings."""

    email_default_send = models.BooleanField(default=True)
    slack_default_send = models.BooleanField(default=True)
    email_footer = models.TextField(null=True, blank=True)
    email_header = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = "Messaging Settings"


class MessagingSettings(Orderable):
    class Meta:
        verbose_name = "Messaging Settings Page"
        constraints = [
            # There is a one-to-one relation for setting-to-site. Therefore, "setting" can be thought of as "site" here.
            models.UniqueConstraint(
                fields=["setting", "message_type"], name="unique_site_type"
            ),
        ]

    setting = ParentalKey(
        to=MessagingSetting,
        on_delete=models.CASCADE,
        related_name="messaging_settings",
    )
    message_type = models.CharField(
        choices=MESSAGES.choices,
        max_length=50,
    )
    email_subject = models.TextField(null=True, blank=True)
    email_message = models.TextField(null=True, blank=True)
    slack_message = models.TextField(null=True, blank=True)
    email_enabled = models.BooleanField()
    slack_enabled = models.BooleanField()

    panels = [
        FieldPanel("message_type", classname="message_type"),
        FieldPanel("email_enabled"),
        FieldPanel("email_subject"),
        FieldPanel("email_message", classname="email_message"),
        FieldPanel("slack_enabled"),
        FieldPanel("slack_message", classname="slack_message"),
    ]
