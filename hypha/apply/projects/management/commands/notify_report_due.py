from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.management.base import BaseCommand
from django.http import HttpRequest
from django.utils import timezone

from hypha.apply.activity.messaging import MESSAGES, messenger
from hypha.apply.projects.models import (
    Project,
    ProjectReminderFrequency,
    ProjectSettings,
)
from hypha.home.models import ApplyHomePage


class Command(BaseCommand):
    help = "Notify users that they have a report due soon"

    def handle(self, *args, **options):
        site = ApplyHomePage.objects.first().get_site()

        # Mock a HTTPRequest in order to pass the site settings into the
        # templates
        request = HttpRequest()
        request.META["SERVER_NAME"] = site.hostname
        request.META["SERVER_PORT"] = site.port
        request.META[settings.SECURE_PROXY_SSL_HEADER] = "https"
        request.session = {}
        request._messages = FallbackStorage(request)

        today = timezone.now().date()

        project_settings = ProjectSettings.objects.filter(site=site).first()
        if not project_settings:
            return

        for frequency in project_settings.reminder_frequencies.all():
            multiplier = (
                -1
                if frequency.relation
                == ProjectReminderFrequency.FrequencyRelation.AFTER
                else 1
            )
            delta = frequency.reminder_days * multiplier

            due_date = today + relativedelta(days=delta)
            for project in Project.objects.in_progress():
                next_report = project.report_config.current_due_report()
                if not next_report:
                    continue

                due_soon = next_report.end_date == due_date
                not_notified_today = (
                    not next_report.notified or next_report.notified.date() != today
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
                        self.style.SUCCESS(f"Notified project: {project.id}")
                    )
