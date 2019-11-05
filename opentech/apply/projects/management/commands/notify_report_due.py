from dateutil.relativedelta import relativedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from opentech.apply.projects.models import Project


class Command(BaseCommand):
    help = 'Notify users that they have a report due soon'

    def add_arguments(self, parser):
        parser.add_argument('days', type=int)

    def handle(self, *args, **options):
        due_date = timezone.now().date() + relativedelta(days=options['days'])
        for project in Project.objects.in_progress():
            next_report = project.report_config.current_due_report()
            if next_report.end_date == due_date:
                # Notify about the due report
                self.stdout.write(
                    self.style.SUCCESS(f'Notified project: {project.id}')
                )
