from dateutil.relativedelta import relativedelta

from django.conf import settings
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.management.base import BaseCommand
from django.http import HttpRequest
from django.utils import timezone
from django.urls import set_urlconf
from opentech.apply.activity.messaging import MESSAGES, messenger
from opentech.apply.home.models import ApplyHomePage
from opentech.apply.projects.models import Project


class Command(BaseCommand):
    help = 'Notify users that they have a report due soon'

    def add_arguments(self, parser):
        parser.add_argument('days_before', type=int)

    def handle(self, *args, **options):
        site = ApplyHomePage.objects.first().get_site()
        set_urlconf('opentech.apply.urls')

        # Mock a HTTPRequest in order to pass the site settings into the
        # templates
        request = HttpRequest()
        request.META['SERVER_NAME'] = site.hostname
        request.META['SERVER_PORT'] = site.port
        request.META[settings.SECURE_PROXY_SSL_HEADER] = 'https'
        request.session = {}
        request._messages = FallbackStorage(request)

        today = timezone.now().date()
        due_date = today + relativedelta(days=options['days_before'])
        for project in Project.objects.in_progress():
            next_report = project.report_config.current_due_report()
            due_soon = next_report.end_date == due_date
            not_notified_today = (
                not next_report.notified or
                next_report.notified.date() != today
            )
            if due_soon and not_notified_today:
                messenger(
                    MESSAGES.REPORT_NOTIFY,
                    request=request,
                    user=None,
                    source=project,
                    related=next_report,
                )
                # Notify about the due report
                next_report.notified = timezone.now()
                next_report.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Notified project: {project.id}')
                )
