import logging
import re
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.translation import gettext as _

from hypha.apply.activity.adapters import SlackAdapter
from hypha.apply.activity.models import Message
from hypha.apply.activity.options import MESSAGES
from hypha.core.mail import MarkdownMail

logger = logging.getLogger(__name__)


def slack_message_to_markdown(msg):
    """Converts messages in the slack format to markdown.

    It converts href in the format <url|title> to [title](url)

    Args:
        msg: slack message as text
    """
    def to_href(match_obj):
        if match_obj.group() is not None:
            return f'[{match_obj.group(2)}]({match_obj.group(1)})'

    return re.sub(r'<(.*)\|(.*)>', to_href, msg)


class Command(BaseCommand):
    help = 'Sent email digest of all unsent activities (last 7 days) in hypha'
    IGNORE_DAYS_BEFORE = 7
    EMAIL_SUBJECT = settings.EMAIL_SUBJECT_PREFIX + _('Activities Summary')

    def handle(self, *args, **options):
        if not settings.ACTIVITY_DIGEST_RECIPIENT_EMAILS:
            raise ImproperlyConfigured(
                'ACTIVITY_DIGEST_RECIPIENT_EMAILS Django settings is required.'
            )

        slack_messages = (
            Message.objects.filter(type=SlackAdapter.adapter_type)
            .select_related('event')
            .order_by('-event__when')
            .filter(sent_in_email_digest=False)
            .filter(
                event__when__gte=(
                    timezone.now() - timedelta(days=self.IGNORE_DAYS_BEFORE)
                ).date()
            )
        )

        # convert slack links to markdown links
        for msg in slack_messages:
            msg.content_markdown = slack_message_to_markdown(msg.content)

        # extract some important activity types into groups
        submissions = [
            m for m in slack_messages if m.event.type == MESSAGES.NEW_SUBMISSION
        ]
        comments = [m for m in slack_messages if m.event.type == MESSAGES.COMMENT]
        reviews = [m for m in slack_messages if m.event.type == MESSAGES.NEW_REVIEW]

        exclude_ids = [m.id for m in submissions + comments + reviews]  # type: ignore
        messages = [m for m in slack_messages if m.id not in exclude_ids]
        total_count = len(slack_messages)
        ctx = {
            'messages': messages,
            'submissions': submissions,
            'comments': comments,
            'reviews': reviews,
            'has_main_sections': bool(exclude_ids),
            'total_count': total_count,
            'ORG_LONG_NAME': settings.ORG_LONG_NAME,
            'ORG_SHORT_NAME': settings.ORG_SHORT_NAME,
            'ORG_URL': settings.ORG_URL,
        }

        if total_count:
            email = MarkdownMail('messages/email/activity_summary.md')
            email.send(
                to=settings.ACTIVITY_DIGEST_RECIPIENT_EMAILS,
                subject=self.EMAIL_SUBJECT,
                from_email=settings.SERVER_EMAIL,
                context=ctx,
            )
            slack_messages.update(sent_in_email_digest=True)
            logger.info('Sent digest email.')
        else:
            logger.info('No email generated/sent, as there are no new activities.')
