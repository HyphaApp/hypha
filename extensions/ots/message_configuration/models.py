from django.db import models
from django.template.loader import get_template
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel, HelpPanel, InlinePanel
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.models import Orderable

from hypha.apply.activity.options import MESSAGES


class MessagingHelpPanel(HelpPanel):
    messages = {
        MESSAGES.NEW_SUBMISSION: "messages/email_defaults/new_submission.html",
        MESSAGES.DRAFT_SUBMISSION: "messages/email_defaults/draft_submission.html",
        MESSAGES.DETERMINATION_OUTCOME: "messages/email_defaults/determination_outcome.html",
        MESSAGES.INVITED_TO_PROPOSAL: "messages/email_defaults/invited_to_proposal.html",
        MESSAGES.READY_FOR_REVIEW: "messages/email_defaults/ready_for_review.html",
        MESSAGES.REVIEWERS_UPDATED: "messages/email_defaults/reviewers_updated.html",
        MESSAGES.REVIEW_REMINDER: "messages/email_defaults/review_reminder.html",
        MESSAGES.APPROVE_PAF: "messages/email_defaults/approve_paf.html",
        MESSAGES.APPROVE_INVOICE: "messages/email_defaults/approve_invoice.html",
    }

    def __init__(self, *args, **kwargs):
        self.email_messages = {}
        for message in MESSAGES:
            if message in MessagingHelpPanel.messages:
                self.email_messages[message] = get_template(
                    MessagingHelpPanel.messages[message]
                ).render()
        super().__init__("", "messaging_help.html", classname="messaging_help_panel")

    class BoundPanel(HelpPanel.BoundPanel):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.email_messages = self.panel.email_messages


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

    panels = [
        MessagingHelpPanel(),
        FieldPanel("email_default_send"),
        FieldPanel("slack_default_send"),
        FieldPanel("email_header"),
        FieldPanel("email_footer"),
        InlinePanel(
            "messaging_settings",
            classname="all_messaging_settings",
        ),
    ]


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
