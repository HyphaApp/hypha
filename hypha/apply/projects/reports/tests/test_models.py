from dateutil.relativedelta import relativedelta
from django.test import TestCase
from django.utils import timezone

from hypha.apply.projects.reports.models import Report, ReportConfig
from hypha.apply.projects.tests.factories import ReportConfigFactory, ReportFactory


class TestReportConfig(TestCase):
    """Tests for the ReportConfig model class which handles report scheduling and management."""

    @property
    def today(self):
        """Returns current date."""
        return timezone.now().date()

    def test_next_date_month_from_now(self):
        """Test that next_date properly calculates a date one month in the future."""
        config = ReportConfigFactory()
        delta = relativedelta(months=1)

        next_date = config.next_date(self.today)

        assert next_date == self.today + delta

    def test_next_date_week_from_now(self):
        """Test that next_date properly calculates a date one week in the future."""
        config = ReportConfigFactory(frequency=ReportConfig.WEEK)
        delta = relativedelta(weeks=1)

        next_date = config.next_date(self.today)

        assert next_date == self.today + delta

    def test_last_report_gets_report_in_past(self):
        config = ReportConfigFactory()
        past_report = ReportFactory(
            project=config.project,
            end_date=self.today - relativedelta(days=3),
        )
        assert past_report == config.last_report()

    def test_last_report_gets_submitted_report_in_past(self):
        config = ReportConfigFactory()
        past_report = ReportFactory(
            project=config.project,
            end_date=self.today - relativedelta(days=3),
            is_submitted=True,
        )
        assert past_report == config.last_report()

    def test_last_report_gets_skipped(self):
        config = ReportConfigFactory()
        skipped_report = ReportFactory(
            project=config.project,
            end_date=self.today + relativedelta(days=3),
            skipped=True,
        )
        assert skipped_report == config.last_report()

    def test_months_always_relative(self):
        config = ReportConfigFactory(occurrence=2)
        last_report = self.today - relativedelta(day=25, months=1)
        next_date = config.next_date(last_report)

        assert next_date == last_report + relativedelta(months=2)

    def test_current_due_report_gets_active_report(self):
        """Test that current_due_report returns the active non-submitted report."""
        config = ReportConfigFactory(disable_reporting=False)
        report = ReportFactory(project=config.project)
        assert config.current_due_report() == report

    def test_no_report_creates_report(self):
        config = ReportConfigFactory(disable_reporting=False)
        report = config.current_due_report()
        # Separate day from month for case where start date + 1 month would exceed next month
        # length (31st Oct to 30th Nov)
        # combined => 31th + 1 month = 30th - 1 day = 29th (wrong)
        # separate => 31th - 1 day = 30th + 1 month = 30th (correct)
        next_due = (
            report.project.start_date - relativedelta(days=1) + relativedelta(months=1)
        )
        assert Report.objects.count() == 1
        assert report.end_date == next_due

    def test_no_report_creates_report_not_in_past(self):
        config = ReportConfigFactory(
            schedule_start=self.today - relativedelta(months=3), disable_reporting=False
        )
        report = config.current_due_report()
        assert Report.objects.count() == 1
        assert report.end_date == self.today

    def test_no_report_creates_report_if_current_skipped(self):
        config = ReportConfigFactory(disable_reporting=False)
        skipped_report = ReportFactory(end_date=self.today + relativedelta(days=3))
        report = config.current_due_report()
        assert Report.objects.count() == 2
        assert skipped_report != report

    def test_no_report_schedule_in_future_creates_report(self):
        config = ReportConfigFactory(
            schedule_start=self.today + relativedelta(days=2), disable_reporting=False
        )
        report = config.current_due_report()
        assert Report.objects.count() == 1
        assert report.end_date == self.today + relativedelta(days=2)

    def test_past_due_report_creates_report(self):
        config = ReportConfigFactory(
            schedule_start=self.today - relativedelta(days=2), disable_reporting=False
        )
        ReportFactory(
            project=config.project, end_date=self.today - relativedelta(days=1)
        )

        # Separate day from month for case where start date + 1 month would exceed next month
        # length (31st Oct to 30th Nov)
        # combined => 31th + 1 month = 30th - 1 day = 29th (wrong)
        # separate => 31th - 1 day = 30th + 1 month = 30th (correct)
        next_due = self.today - relativedelta(days=1) + relativedelta(months=1)

        report = config.current_due_report()
        assert Report.objects.count() == 2
        assert report.end_date == next_due

    def test_today_schedule_gets_report_today(self):
        config = ReportConfigFactory(disable_reporting=False, schedule_start=self.today)
        assert config.current_due_report().end_date == self.today

    def test_past_due_report_future_schedule_creates_report(self):
        config = ReportConfigFactory(
            schedule_start=self.today + relativedelta(days=3), disable_reporting=False
        )
        ReportFactory(
            project=config.project, end_date=self.today - relativedelta(days=1)
        )

        report = config.current_due_report()
        assert Report.objects.count() == 2
        assert report.end_date == self.today + relativedelta(days=3)

    def test_submitted_report_unaffected(self):
        config = ReportConfigFactory()
        report = ReportFactory(
            is_submitted=True,
            project=config.project,
            end_date=self.today + relativedelta(days=1),
        )
        next_report = config.current_due_report()
        assert report != next_report

    def test_past_due(self):
        """Test that past_due_reports includes overdue reports."""
        report = ReportFactory(past_due=True)
        config = report.project.report_config
        self.assertQuerysetEqual(
            config.past_due_reports(), [report], transform=lambda x: x
        )

    def test_past_due_has_drafts(self):
        """Test that past_due_reports includes draft reports."""
        report = ReportFactory(past_due=True, is_draft=True)
        config = report.project.report_config
        self.assertQuerysetEqual(
            config.past_due_reports(), [report], transform=lambda x: x
        )

    def test_past_due_no_submitted(self):
        """Test that past_due_reports excludes submitted reports."""
        report = ReportFactory(is_submitted=True, past_due=True)
        config = report.project.report_config
        self.assertQuerysetEqual(config.past_due_reports(), [], transform=lambda x: x)

    def test_past_due_no_future(self):
        """Test that past_due_reports excludes future reports."""
        report = ReportFactory(end_date=self.today + relativedelta(days=1))
        config = report.project.report_config
        self.assertQuerysetEqual(config.past_due_reports(), [], transform=lambda x: x)

    def test_past_due_no_skipped(self):
        """Test that past_due_reports excludes skipped reports."""
        report = ReportFactory(skipped=True, past_due=True)
        config = report.project.report_config
        self.assertQuerysetEqual(config.past_due_reports(), [], transform=lambda x: x)


class TestReport(TestCase):
    """Tests for the Report model class."""

    @property
    def today(self):
        return timezone.now().date()

    def from_today(self, days):
        return self.today + relativedelta(days=days)

    def test_not_late_if_one_ahead(self):
        """Test that report is not considered late if one report ahead exists."""
        report = ReportFactory(end_date=self.from_today(-3))
        ReportFactory(project=report.project)
        assert not report.is_very_late

    def test_late_if_two_weeks_behind(self):
        """Test that report is considered late if two weeks overdue."""
        report = ReportFactory(end_date=self.from_today(-15))
        assert report.is_very_late

    def test_not_late_if_two_ahead_but_one_in_future(self):
        report = ReportFactory(end_date=self.from_today(-3))
        ReportFactory(project=report.project)
        ReportFactory(end_date=self.from_today(2), project=report.project)
        assert not report.is_very_late

    def test_start_date(self):
        """Test start date calculation for reports."""
        yesterday = self.from_today(-1)
        ReportFactory(end_date=yesterday)
        report = ReportFactory(end_date=self.from_today(1))
        assert report.start_date == self.today

    def test_start_date_with_submitted(self):
        yesterday = self.from_today(-1)
        ReportFactory(end_date=yesterday)
        report = ReportFactory(end_date=self.from_today(1), is_submitted=True)
        assert report.start_date == self.today

    def test_queryset_done_includes_submitted(self):
        """Test that done() queryset includes submitted reports."""
        report = ReportFactory(is_submitted=True)
        self.assertQuerysetEqual(Report.objects.done(), [report], transform=lambda x: x)

    def test_queryset_done_includes_skipped(self):
        """Test that done() queryset includes skipped reports."""
        report = ReportFactory(skipped=True)
        self.assertQuerysetEqual(Report.objects.done(), [report], transform=lambda x: x)

    def test_queryset_done_doesnt_includes_draft(self):
        """Test that done() queryset excludes draft reports."""
        ReportFactory(is_draft=True)
        self.assertQuerysetEqual(Report.objects.done(), [], transform=lambda x: x)

    def test_queryset_done_doesnt_includes_to_do(self):
        """Test that done() queryset excludes to-do reports."""
        ReportFactory()
        self.assertQuerysetEqual(Report.objects.done(), [], transform=lambda x: x)
