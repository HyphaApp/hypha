from django.conf import settings
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.management.base import BaseCommand
from django.http import HttpRequest
from django.urls import set_urlconf
from django.utils import timezone

from hypha.apply.activity.messaging import messenger
from hypha.apply.funds.models import Reminder
from hypha.apply.home.models import ApplyHomePage


class Command(BaseCommand):
    help = 'Send reminders'

    def handle(self, *args, **options):
        site = ApplyHomePage.objects.first().get_site()
        set_urlconf('hypha.apply.urls')

        # Mock a HTTPRequest in order to pass the site settings into the
        # templates
        request = HttpRequest()
        request.META['SERVER_NAME'] = site.hostname
        request.META['SERVER_PORT'] = site.port
        request.META[settings.SECURE_PROXY_SSL_HEADER] = 'https'
        request.session = {}
        request._messages = FallbackStorage(request)

        for reminder in Reminder.objects.filter(sent=False, time__lte=timezone.now()):
            messenger(
                reminder.action_message,
                request=request,
                user=None,
                source=reminder.submission,
                related=reminder,
            )
            self.stdout.write(
                self.style.SUCCESS(f'Reminder sent: {reminder.id}')
            )
            reminder.sent = True
            reminder.save()
