from io import StringIO

from dateutil.relativedelta import relativedelta
from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from hypha.apply.projects.models.project import (
    ProjectReminderFrequency,
    ProjectSettings,
)
from hypha.apply.projects.tests.factories import ProjectFactory
from hypha.home.factories import ApplySiteFactory

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

    @override_settings(
        WAGTAILADMIN_BASE_URL="https://apply.example.org", SEND_MESSAGES=True
    )
    def test_notification_links_use_the_configured_base_url(self):
        """The default Wagtail site record uses port 80, which used to leak into
        the links as `https://host:80/...`."""
        in_a_week = timezone.now() + relativedelta(days=7)
        ReportConfigFactory(
            disable_reporting=False, schedule_start=in_a_week, project__in_progress=True
        )

        call_command("notify_report_due", stdout=StringIO())

        assert len(mail.outbox) > 0
        body = mail.outbox[0].body
        assert "https://apply.example.org/" in body
        assert ":80/" not in body
