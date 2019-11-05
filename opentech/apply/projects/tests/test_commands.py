from io import StringIO

from dateutil.relativedelta import relativedelta

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from .factories import (
    ProjectFactory,
    ReportConfigFactory,
    ReportFactory,
)


class TestNotifyReportDue(TestCase):
    def test_notify_report_due_in_7_days(self):
        in_a_week = timezone.now() + relativedelta(days=7)
        ReportConfigFactory(schedule_start=in_a_week, project__in_progress=True)
        out = StringIO()
        call_command('notify_report_due', 7, stdout=out)
        self.assertIn('Notified project', out.getvalue())

    def test_dont_notify_report_due_in_7_days_already_submitted(self):
        in_a_week = timezone.now() + relativedelta(days=7)
        config = ReportConfigFactory(schedule_start=in_a_week)
        ReportFactory(
            project=config.project,
            is_submitted=True,
            end_date=config.schedule_start,
        )
        out = StringIO()
        call_command('notify_report_due', 7, stdout=out)
        self.assertNotIn('Notified project', out.getvalue())

    def test_dont_notify_project_not_in_progress(self):
        ProjectFactory()
        out = StringIO()
        call_command('notify_report_due', 7, stdout=out)
        self.assertNotIn('Notified project', out.getvalue())

    def test_dont_notify_project_closed(self):
        ProjectFactory()
        out = StringIO()
        call_command('notify_report_due', 7, stdout=out)
        self.assertNotIn('Notified project', out.getvalue())
