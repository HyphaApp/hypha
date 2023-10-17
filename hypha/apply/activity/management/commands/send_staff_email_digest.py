import logging
import re
from collections import defaultdict
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.translation import gettext as _

from hypha.apply.activity.adapters import SlackAdapter
from hypha.apply.activity.models import Message
from hypha.apply.activity.options import MESSAGES
from hypha.core.mail import MarkdownMail

logger = logging.getLogger(__name__)


def groupby_fund_lab_id(messages):
    fund_map_msgs_map = defaultdict(list)
    for msg in messages:
        id = extract_fund_or_lab_property(msg.event, "id")
        if id:
            fund_map_msgs_map[id].append(msg)
    return fund_map_msgs_map.items()


def extract_fund_or_lab_property(event, prop):
    """Retrieve properties from fund or lab, if present.

                     ┌─────┐
                     │Fund │
                     └─────┘
        event.source    │
                  ┌─────┼────────────┐
                  │  ┌──▼──┐ ┌─────┐ │
                  │  │Round│ │ Lab │ │
                  │  └──┬──┘ └┬────┘ │
                  └─────┼─────┼──────┘
                        └──┬──┘
                           │
                           ▼
    Args:
        event: Event ModelClass instance

    Returns:
        An array of emails or empty list.
    """
    if hasattr(event.source, "get_from_parent"):
        if event.source.round:
            # Get attribute from the parent of round
            fund = event.source.round.get_parent()
            return getattr(fund.specific, prop)

        # extract from the lab
        return event.source.get_from_parent(prop)

    return None


def slack_message_to_markdown(msg):
    """Converts messages in the slack format to markdown.

    It converts href in the format <url|title> to [title](url)

    Args:
        msg: slack message as text
    """

    def to_href(match_obj):
        if match_obj.group() is not None:
            return f"[{match_obj.group(2)}]({match_obj.group(1)})"

    return re.sub(r"<(.*)\|(.*)>", to_href, msg)


def prepare_and_send_activity_digest_email(to, subject, slack_messages):
    # extract some important activity types into groups
    submissions = [m for m in slack_messages if m.event.type == MESSAGES.NEW_SUBMISSION]
    comments = [m for m in slack_messages if m.event.type == MESSAGES.COMMENT]
    reviews = [m for m in slack_messages if m.event.type == MESSAGES.NEW_REVIEW]

    exclude_ids = [m.id for m in submissions + comments + reviews]  # type: ignore
    messages = [m for m in slack_messages if m.id not in exclude_ids]
    total_count = len(slack_messages)
    ctx = {
        "messages": messages,
        "submissions": submissions,
        "comments": comments,
        "reviews": reviews,
        "has_main_sections": bool(exclude_ids),
        "total_count": total_count,
        "ORG_LONG_NAME": settings.ORG_LONG_NAME,
        "ORG_SHORT_NAME": settings.ORG_SHORT_NAME,
        "ORG_URL": settings.ORG_URL,
    }

    if total_count:
        email = MarkdownMail("messages/email/activity_summary.md")
        email.send(
            to=to,
            subject=subject,
            from_email=settings.SERVER_EMAIL,
            context=ctx,
        )
        logger.info(f"Sent activity digest email to {to}")
    else:
        logger.info("No email generated/sent, as there are no new activities.")


class Command(BaseCommand):
    """Management command to send a summary of activities in hypha to configured
    emails.

    It sends all the activities to the emails set in "ACTIVITY_DIGEST_RECIPIENT_EMAILS",
    if it is set.

    It also checks for messages that belong a fund or lab, if a lab or fund has
    "activity_digest_recipient_emails" property set, it also sends the digest related
    to that fund or lab to that email.
    """

    help = "Sent email digest of all unsent activities (last 7 days) in hypha"
    IGNORE_DAYS_BEFORE = 7

    def handle(self, *args, **options):
        slack_messages = (
            Message.objects.filter(type=SlackAdapter.adapter_type)
            .select_related("event")
            .order_by("-event__when")
            .filter(sent_in_email_digest=False)
            .filter(
                event__when__gte=(
                    timezone.now() - timedelta(days=self.IGNORE_DAYS_BEFORE)
                ).date()
            )
        )
        # convert slack links and extract the fund/lab emails
        for msg in slack_messages:
            msg.content_markdown = slack_message_to_markdown(msg.content)

        # Send global activity digest if "ACTIVITY_DIGEST_RECIPIENT_EMAILS" settings is set.
        if settings.ACTIVITY_DIGEST_RECIPIENT_EMAILS:
            prepare_and_send_activity_digest_email(
                to=settings.ACTIVITY_DIGEST_RECIPIENT_EMAILS,
                subject=settings.EMAIL_SUBJECT_PREFIX + _("Summary of all activities"),
                slack_messages=slack_messages,
            )
        else:
            logger.info(
                "Global activity digest email not sent. Set ACTIVITY_DIGEST_RECIPIENT_EMAILS setting to enable it."
            )

        # Send digest of for funds that has "activity_digest_recipient_emails" set.
        for _id, messages in groupby_fund_lab_id(slack_messages):
            emails = extract_fund_or_lab_property(
                messages[0].event, "activity_digest_recipient_emails"
            )
            if not emails:
                continue
            title = extract_fund_or_lab_property(messages[0].event, "title")
            subject = settings.EMAIL_SUBJECT_PREFIX + _("Activities Summary - ") + title

            prepare_and_send_activity_digest_email(
                subject=subject,
                to=emails,
                slack_messages=messages,
            )

            # mark as sent
            Message.objects.filter(id__in=[m.id for m in messages]).update(
                sent_in_email_digest=True
            )

        if settings.ACTIVITY_DIGEST_RECIPIENT_EMAILS:
            slack_messages.update(sent_in_email_digest=True)  # mark as sent
