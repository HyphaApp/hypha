from io import StringIO

from dateutil.relativedelta import relativedelta
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from hypha.apply.projects.models.project import (
    ProjectReminderFrequency,
    ProjectSettings,
)
from hypha.apply.projects.tests.factories import ProjectFactory
from hypha.home.factories import ApplySiteFactory
from hypha.home.models import ApplyHomePage

from .factories import ReportConfigFactory, ReportFactory


class TestNotifyReportDue(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        apply_site = ApplySiteFactory()
        cls.project_settings, _ = ProjectSettings.objects.get_or_create(
            site_id=apply_site.id,
        )
        cls.project_settings.reminder_frequencies = [
            ProjectReminderFrequency.objects.create(
                page=cls.project_settings,
                reminder_days=7,
                relation=ProjectReminderFrequency.FrequencyRelation.BEFORE,
            ),
        ]
        cls.project_settings.save()

    def test_notify_report_due_in_7_days(self):
        in_a_week = timezone.now() + relativedelta(days=7)
        ReportConfigFactory(
            disable_reporting=False, schedule_start=in_a_week, project__in_progress=True
        )
        out = StringIO()

        with self.settings(
            ALLOWED_HOSTS=[ApplyHomePage.objects.first().get_site().hostname]
        ):
            call_command("notify_report_due", stdout=out)
        assert "Notified project" in out.getvalue()

    def test_dont_notify_report_due_in_7_days_already_submitted(self):
        in_a_week = timezone.now() + relativedelta(days=7)
        config = ReportConfigFactory(
            schedule_start=in_a_week, project__in_progress=True
        )
        ReportFactory(
            project=config.project,
            is_submitted=True,
            end_date=config.schedule_start,
        )
        out = StringIO()
        with self.settings(
            ALLOWED_HOSTS=[ApplyHomePage.objects.first().get_site().hostname]
        ):
            call_command("notify_report_due", stdout=out)
        assert "Notified project" not in out.getvalue()

    def test_dont_notify_already_notified(self):
        in_a_week = timezone.now() + relativedelta(days=7)
        config = ReportConfigFactory(
            schedule_start=in_a_week, project__in_progress=True
        )
        ReportFactory(
            project=config.project,
            end_date=config.schedule_start,
            notified=timezone.now(),
        )
        out = StringIO()
        call_command("notify_report_due", stdout=out)
        assert "Notified project" not in out.getvalue()

    def test_dont_notify_project_not_in_progress(self):
        ProjectFactory()
        out = StringIO()
        call_command("notify_report_due", stdout=out)
        assert "Notified project" not in out.getvalue()

    def test_dont_notify_project_complete(self):
        ProjectFactory(is_complete=True)
        out = StringIO()
        call_command("notify_report_due", stdout=out)
        assert "Notified project" not in out.getvalue()
