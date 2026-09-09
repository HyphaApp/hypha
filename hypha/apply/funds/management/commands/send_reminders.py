from django.core.management.base import BaseCommand
from django.utils import timezone
from wagtail.coreutils import get_dummy_request
from wagtail.models import Site

from hypha.apply.activity.messaging import messenger
from hypha.apply.funds.models import Reminder


class Command(BaseCommand):
    help = "Send reminders"

    def handle(self, *args, **options):
        # The messenger expects a request. Links in the notifications are built
        # from `get_base_url()`, not from the request.
        request = get_dummy_request(
            site=Site.objects.filter(is_default_site=True).first()
        )

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
