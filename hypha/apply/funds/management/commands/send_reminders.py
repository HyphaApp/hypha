from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.management.base import BaseCommand
from django.http import HttpRequest
from django.utils import timezone

from hypha.apply.activity.messaging import messenger
from hypha.apply.funds.models import Reminder


class Command(BaseCommand):
    help = "Send reminders"

    def handle(self, *args, **options):
        # Mock a HTTPRequest as the messenger expects one. Links in the
        # notifications are built from `get_base_url()`, not from the request.
        request = HttpRequest()
        request.session = {}
        request._messages = FallbackStorage(request)

        for reminder in Reminder.objects.filter(
            sent=False, time__lte=timezone.now()
        ).select_related("submission"):
            messenger(
                reminder.action_message,
                request=request,
                user=None,
                source=reminder.submission,
                related=reminder,
            )
            self.stdout.write(self.style.SUCCESS(f"Reminder sent: {reminder.id}"))
            reminder.sent = True
            reminder.save()
