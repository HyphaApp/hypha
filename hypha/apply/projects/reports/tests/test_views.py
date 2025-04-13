import json

from dateutil.relativedelta import relativedelta
from django.urls import reverse
from django.utils import timezone

from hypha.apply.funds.models.forms import ApplicationBaseProjectReportForm
from hypha.apply.projects.models.project import (
    CLOSING,
    COMPLETE,
    INVOICING_AND_REPORTING,
    ProjectReportForm,
)
from hypha.apply.projects.reports.tests.utils import FORM_FIELDS
from hypha.apply.projects.tests.factories import (
    ProjectFactory,
    ReportConfigFactory,
    ReportFactory,
    ReportVersionFactory,
)
from hypha.apply.users.tests.factories import (
    ApplicantFactory,
    StaffFactory,
)
from hypha.apply.utils.testing.tests import BaseViewTestCase


class TestReportPrivateMedia(BaseViewTestCase):
    """Tests access to private media files attached to reports"""

    base_view_name = "file"
    url_name = "funds:projects:reports:{}"
    user_factory = StaffFactory

    def get_kwargs(self, instance):
        return {
            "pk": instance.report.report.pk,
            "file_pk": instance.pk,
        }


class TestStaffSubmitReport(BaseViewTestCase):
    """Tests staff ability to submit and edit project reports"""

    base_view_name = "edit"
    url_name = "funds:projects:reports:{}"
    user_factory = StaffFactory
    report_form_id = None

    def setUp(self):
        super().setUp()
        report_form, _ = ProjectReportForm.objects.get_or_create(
            name="Test Form",
            form_fields=FORM_FIELDS,
        )
        self.report_form_id = report_form.id

    def get_kwargs(self, instance):
        return {
            "pk": instance.pk,
        }

    def test_get_page_for_inprogress_project(self):
        """Tests accessing report page for in-progress project"""
        report = ReportFactory(project__status=INVOICING_AND_REPORTING)
        ApplicationBaseProjectReportForm.objects.get_or_create(
            application_id=report.project.submission.page.specific.id,
            form_id=self.report_form_id,
        )
        response = self.get_page(report)
        assert report.project.title in response.content.decode()

    def test_cant_get_page_for_closing_and_complete_project(self):
        """Tests that report pages are inaccessible for closed/completed projects"""
        report = ReportFactory(project__status=CLOSING)
        ApplicationBaseProjectReportForm.objects.get_or_create(
            application_id=report.project.submission.page.specific.id,
            form_id=self.report_form_id,
        )
        response = self.get_page(report)
        assert response.status_code == 403

        report = ReportFactory(project__status=COMPLETE)
        response = self.get_page(report)
        assert response.status_code == 403

    def test_submit_report(self):
        """Tests submitting a report with valid data"""
        report = ReportFactory(project__status=INVOICING_AND_REPORTING)
        ApplicationBaseProjectReportForm.objects.get_or_create(
            application_id=report.project.submission.page.specific.id,
            form_id=self.report_form_id,
        )
        response = self.post_page(
            report, {"012a4f29-0882-4b1c-b567-aede1b601d4a": "11"}
        )
        report.refresh_from_db()
        self.assertRedirects(response, report.project.get_absolute_url())
        assert report.versions.first().form_data == {
            "012a4f29-0882-4b1c-b567-aede1b601d4a": "11"
        }
        assert report.versions.first() == report.current
        assert report.current.author == self.user
        assert report.draft is None

    def test_cant_submit_report_for_closing_and_complete_project(self):
        """Tests reports cannot be submitted for closed/completed projects"""
        report = ReportFactory(project__status=CLOSING)
        ApplicationBaseProjectReportForm.objects.get_or_create(
            application_id=report.project.submission.page.specific.id,
            form_id=self.report_form_id,
        )
        response = self.post_page(
            report, {"012a4f29-0882-4b1c-b567-aede1b601d4a": "13"}
        )
        assert response.status_code == 403

        report = ReportFactory(project__status=COMPLETE)
        ApplicationBaseProjectReportForm.objects.get_or_create(
            application_id=report.project.submission.page.specific.id,
            form_id=self.report_form_id,
        )
        response = self.post_page(
            report, {"012a4f29-0882-4b1c-b567-aede1b601d4a": "13"}
        )
        assert response.status_code == 403

    def test_submit_private_report(self):
        """Tests submission of private report content"""
        report = ReportFactory(project__status=INVOICING_AND_REPORTING)
        # Link the single-field report_form to the Fund associated with this Submission.
        ApplicationBaseProjectReportForm.objects.get_or_create(
            application_id=report.project.submission.page.specific.id,
            form_id=self.report_form_id,
        )
        response = self.post_page(
            report, {"012a4f29-0882-4b1c-b567-aede1b601d4a": "17"}
        )
        report.refresh_from_db()
        assert response.status_code == 200
        assert report.versions.first().form_data == {
            "012a4f29-0882-4b1c-b567-aede1b601d4a": "17"
        }
        assert report.versions.first() == report.current
        assert report.current.author == self.user
        assert report.draft is None

    def test_cant_submit_blank_report(self):
        """Tests that blank reports cannot be submitted"""
        report = ReportFactory(project__status=INVOICING_AND_REPORTING)
        ApplicationBaseProjectReportForm.objects.get_or_create(
            application_id=report.project.submission.page.specific.id,
            form_id=self.report_form_id,
        )
        response = self.post_page(report, {})
        report.refresh_from_db()
        assert response.status_code == 200
        assert report.versions.count() == 0

    def test_save_report_draft(self):
        """Tests saving report as draft"""
        report = ReportFactory(project__status=INVOICING_AND_REPORTING)
        ApplicationBaseProjectReportForm.objects.get_or_create(
            application_id=report.project.submission.page.specific.id,
            form_id=self.report_form_id,
        )
        response = self.post_page(
            report, {"012a4f29-0882-4b1c-b567-aede1b601d4a": "19", "save": "Save"}
        )
        report.refresh_from_db()
        assert response.status_code == 200
        assert report.versions.first().form_data == {
            "012a4f29-0882-4b1c-b567-aede1b601d4a": "19"
        }
        assert report.versions.first() == report.draft
        assert report.current is None

    def test_save_report_with_draft(self):
        """Tests saving report that already has draft version"""
        report = ReportFactory(is_draft=True, project__status=INVOICING_AND_REPORTING)
        ApplicationBaseProjectReportForm.objects.get_or_create(
            application_id=report.project.submission.page.specific.id,
            form_id=self.report_form_id,
        )
        assert report.versions.first() == report.draft
        response = self.post_page(
            report, {"012a4f29-0882-4b1c-b567-aede1b601d4a": "23"}
        )
        report.refresh_from_db()
        assert response.status_code == 200
        assert report.versions.last().form_data == {
            "012a4f29-0882-4b1c-b567-aede1b601d4a": "23"
        }
        assert report.versions.last() == report.current
        assert report.draft is None

    def test_edit_submitted_report(self):
        """Tests editing an already submitted report"""
        report = ReportFactory(
            is_submitted=True,
            project__status=INVOICING_AND_REPORTING,
            form_fields=json.dumps(FORM_FIELDS),
        )
        ApplicationBaseProjectReportForm.objects.get_or_create(
            application_id=report.project.submission.page.specific.id,
            form_id=self.report_form_id,
        )
        assert report.versions.first() == report.current
        response = self.post_page(
            report, {"012a4f29-0882-4b1c-b567-aede1b601d4a": "29", "save": " Save"}
        )
        report.refresh_from_db()
        self.assertRedirects(response, report.project.get_absolute_url())
        assert (
            report.versions.last().form_data["012a4f29-0882-4b1c-b567-aede1b601d4a"]
            == "29"
        )
        assert report.versions.last() == report.draft
        assert report.versions.first() == report.current

    def test_resubmit_submitted_report(self):
        """Tests resubmitting a previously submitted report"""
        yesterday = timezone.now() - relativedelta(days=1)
        version = ReportVersionFactory(
            report__project__status=INVOICING_AND_REPORTING,
            submitted=yesterday,
        )
        report = version.report
        report.form_fields = json.dumps(FORM_FIELDS)
        ApplicationBaseProjectReportForm.objects.get_or_create(
            application_id=report.project.submission.page.specific.id,
            form_id=self.report_form_id,
        )
        report.current = version
        report.submitted = version.submitted
        report.save()
        assert report.submitted == yesterday
        assert report.versions.first() == report.current
        response = self.post_page(
            report, {"012a4f29-0882-4b1c-b567-aede1b601d4a": "31"}
        )
        report.refresh_from_db()
        self.assertRedirects(response, report.project.get_absolute_url())
        assert report.versions.last().form_data == {
            "012a4f29-0882-4b1c-b567-aede1b601d4a": "31"
        }
        assert report.versions.last() == report.current
        assert report.draft is None
        assert report.submitted.date() == yesterday.date()
        assert report.current.submitted.date() == timezone.now().date()

    def test_cant_submit_future_report(self):
        """Tests that future dated reports cannot be submitted"""
        submitted_report = ReportFactory(
            end_date=timezone.now() + relativedelta(days=1),
            is_submitted=True,
            project__status=INVOICING_AND_REPORTING,
        )
        ApplicationBaseProjectReportForm.objects.get_or_create(
            application_id=submitted_report.project.submission.page.specific.id,
            form_id=self.report_form_id,
        )
        future_report = ReportFactory(
            end_date=timezone.now() + relativedelta(days=3),
            project=submitted_report.project,
        )
        response = self.post_page(
            future_report, {"012a4f29-0882-4b1c-b567-aede1b601d4a": "37"}
        )
        assert response.status_code == 403


class TestApplicantSubmitReport(BaseViewTestCase):
    """Tests applicant's ability to submit and manage reports"""

    base_view_name = "edit"
    url_name = "funds:projects:reports:{}"
    user_factory = ApplicantFactory
    report_form_id = None

    def setUp(self):
        super().setUp()
        report_form, _ = ProjectReportForm.objects.get_or_create(
            name="Test Form",
            form_fields=FORM_FIELDS,
        )
        self.report_form_id = report_form.id

    def get_kwargs(self, instance):
        return {
            "pk": instance.pk,
        }

    def test_get_own_report_for_inprogress_project(self):
        """Tests accessing own report for in-progress project"""
        report = ReportFactory(
            project__status=INVOICING_AND_REPORTING, project__user=self.user
        )
        ApplicationBaseProjectReportForm.objects.get_or_create(
            application_id=report.project.submission.page.specific.id,
            form_id=self.report_form_id,
        )
        response = self.get_page(report)
        assert report.project.title in response.content.decode()

    def test_cant_get_own_report_for_closing_and_complete_project(self):
        """Tests that own reports are inaccessible for closed/completed projects"""
        report = ReportFactory(project__status=CLOSING, project__user=self.user)
        ApplicationBaseProjectReportForm.objects.get_or_create(
            application_id=report.project.submission.page.specific.id,
            form_id=self.report_form_id,
        )
        response = self.get_page(report)
        assert response.status_code == 403

        report = ReportFactory(project__status=COMPLETE, project__user=self.user)
        ApplicationBaseProjectReportForm.objects.get_or_create(
            application_id=report.project.submission.page.specific.id,
            form_id=self.report_form_id,
        )
        response = self.get_page(report)
        assert response.status_code == 403

    def test_cant_get_other_report(self):
        """Tests that applicants cannot access other users' reports"""
        report = ReportFactory(project__status=INVOICING_AND_REPORTING)
        ApplicationBaseProjectReportForm.objects.get_or_create(
            application_id=report.project.submission.page.specific.id,
            form_id=self.report_form_id,
        )
        response = self.get_page(report)
        assert response.status_code == 403

    def test_submit_own_report(self):
        """Tests submitting own report"""
        report = ReportFactory(
            project__status=INVOICING_AND_REPORTING, project__user=self.user
        )
        ApplicationBaseProjectReportForm.objects.get_or_create(
            application_id=report.project.submission.page.specific.id,
            form_id=self.report_form_id,
        )
        response = self.post_page(
            report, {"012a4f29-0882-4b1c-b567-aede1b601d4a": "37"}
        )
        report.refresh_from_db()
        self.assertRedirects(response, report.project.get_absolute_url())
        assert report.versions.first().form_data == {
            "012a4f29-0882-4b1c-b567-aede1b601d4a": "37"
        }
        assert report.versions.first() == report.current
        assert report.current.author == self.user

    def test_submit_private_report(self):
        """Tests submission of private report content"""
        report = ReportFactory(
            project__status=INVOICING_AND_REPORTING, project__user=self.user
        )
        ApplicationBaseProjectReportForm.objects.get_or_create(
            application_id=report.project.submission.page.specific.id,
            form_id=self.report_form_id,
        )
        response = self.post_page(
            report, {"012a4f29-0882-4b1c-b567-aede1b601d4a": "41"}
        )
        report.refresh_from_db()
        assert response.status_code == 200
        assert report.versions.first().form_data == {
            "012a4f29-0882-4b1c-b567-aede1b601d4a": "41"
        }
        assert report.versions.first() == report.current
        assert report.current.author == self.user
        assert report.draft is None

    def test_cant_submit_blank_report(self):
        """Tests that blank reports cannot be submitted"""
        report = ReportFactory(
            project__status=INVOICING_AND_REPORTING, project__user=self.user
        )
        ApplicationBaseProjectReportForm.objects.get_or_create(
            application_id=report.project.submission.page.specific.id,
            form_id=self.report_form_id,
        )
        response = self.post_page(report, {})
        report.refresh_from_db()
        assert response.status_code == 200
        assert report.versions.count() == 0

    def test_save_report_draft(self):
        """Tests saving report as draft"""
        report = ReportFactory(
            project__status=INVOICING_AND_REPORTING, project__user=self.user
        )
        ApplicationBaseProjectReportForm.objects.get_or_create(
            application_id=report.project.submission.page.specific.id,
            form_id=self.report_form_id,
        )
        response = self.post_page(
            report, {"012a4f29-0882-4b1c-b567-aede1b601d4a": "43", "save": "Save"}
        )
        report.refresh_from_db()
        self.assertRedirects(response, report.project.get_absolute_url())
        assert report.versions.first().form_data == {
            "012a4f29-0882-4b1c-b567-aede1b601d4a": "43"
        }
        assert report.versions.first() == report.draft
        assert report.current is None

    def test_save_report_with_draft(self):
        """Tests saving report that already has draft version"""
        report = ReportFactory(
            project__status=INVOICING_AND_REPORTING,
            is_draft=True,
            project__user=self.user,
        )
        ApplicationBaseProjectReportForm.objects.get_or_create(
            application_id=report.project.submission.page.specific.id,
            form_id=self.report_form_id,
        )
        assert report.versions.first() == report.draft
        response = self.post_page(
            report, {"012a4f29-0882-4b1c-b567-aede1b601d4a": "47"}
        )
        report.refresh_from_db()
        self.assertRedirects(response, report.project.get_absolute_url())
        assert report.versions.last().form_data == {
            "012a4f29-0882-4b1c-b567-aede1b601d4a": "47"
        }
        assert report.versions.last() == report.current
        assert report.draft is None

    def test_cant_edit_submitted_report(self):
        """Tests that submitted reports cannot be edited"""
        report = ReportFactory(
            project__status=INVOICING_AND_REPORTING,
            is_submitted=True,
            project__user=self.user,
        )
        ApplicationBaseProjectReportForm.objects.get_or_create(
            application_id=report.project.submission.page.specific.id,
            form_id=self.report_form_id,
        )
        assert report.versions.first() == report.current
        response = self.post_page(
            report, {"public_content": "Some text", "save": " Save"}
        )
        assert response.status_code == 403

    def test_cant_submit_other_report(self):
        """Tests that applicants cannot submit other users' reports"""
        report = ReportFactory(project__status=INVOICING_AND_REPORTING)
        ApplicationBaseProjectReportForm.objects.get_or_create(
            application_id=report.project.submission.page.specific.id,
            form_id=self.report_form_id,
        )
        response = self.post_page(
            report, {"012a4f29-0882-4b1c-b567-aede1b601d4a": "53"}
        )
        assert response.status_code == 403


class TestStaffReportDetail(BaseViewTestCase):
    """Tests staff access to report details"""

    base_view_name = "detail"
    url_name = "funds:projects:reports:{}"
    user_factory = StaffFactory

    def get_kwargs(self, instance):
        return {
            "pk": instance.pk,
        }

    def test_can_access_submitted_report(self):
        """Tests staff can access submitted reports"""
        report = ReportFactory(
            project__status=INVOICING_AND_REPORTING, is_submitted=True
        )
        response = self.get_page(report)
        assert response.status_code == 200

        report = ReportFactory(project__status=CLOSING, is_submitted=True)
        response = self.get_page(report)
        assert response.status_code == 200

        report = ReportFactory(project__status=COMPLETE, is_submitted=True)
        response = self.get_page(report)
        assert response.status_code == 200

    def test_cant_access_skipped_report(self):
        """Tests staff cannot access skipped reports"""
        report = ReportFactory(project__status=INVOICING_AND_REPORTING, skipped=True)
        response = self.get_page(report)
        assert response.status_code == 403

    def test_cant_access_draft_report(self):
        """Tests staff cannot access draft reports"""
        report = ReportFactory(project__status=INVOICING_AND_REPORTING, is_draft=True)
        response = self.get_page(report)
        assert response.status_code == 403

    def test_cant_access_future_report(self):
        """Tests staff cannot access future dated reports"""
        report = ReportFactory(
            project__status=INVOICING_AND_REPORTING,
            end_date=timezone.now() + relativedelta(days=1),
        )
        response = self.get_page(report)
        assert response.status_code == 403


class TestApplicantReportDetail(BaseViewTestCase):
    """Tests applicant access to report details"""

    base_view_name = "detail"
    url_name = "funds:projects:reports:{}"
    user_factory = StaffFactory

    def get_kwargs(self, instance):
        return {
            "pk": instance.pk,
        }

    def test_can_access_own_submitted_report(self):
        """Tests applicants can access their own submitted reports"""
        report = ReportFactory(
            project__status=INVOICING_AND_REPORTING,
            is_submitted=True,
            project__user=self.user,
        )
        response = self.get_page(report)
        assert response.status_code == 200

    def test_cant_access_own_draft_report(self):
        """Tests applicants cannot access their own draft reports"""
        report = ReportFactory(
            project__status=INVOICING_AND_REPORTING,
            is_draft=True,
            project__user=self.user,
        )
        response = self.get_page(report)
        assert response.status_code == 403

    def test_cant_access_own_future_report(self):
        """Tests applicants cannot access their own future dated reports"""
        report = ReportFactory(
            project__status=INVOICING_AND_REPORTING,
            end_date=timezone.now() + relativedelta(days=1),
            project__user=self.user,
        )
        response = self.get_page(report)
        assert response.status_code == 403

    def test_cant_access_other_submitted_report(self):
        """Tests applicants cannot access other users' submitted reports"""
        report = ReportFactory(
            project__status=INVOICING_AND_REPORTING, is_submitted=True
        )
        response = self.get_page(report)
        assert response.status_code == 200

    def test_cant_access_other_draft_report(self):
        """Tests applicants cannot access other users' draft reports"""
        report = ReportFactory(project__status=INVOICING_AND_REPORTING, is_draft=True)
        response = self.get_page(report)
        assert response.status_code == 403

    def test_cant_access_other_future_report(self):
        """Tests applicants cannot access other users' future dated reports"""
        report = ReportFactory(
            project__status=INVOICING_AND_REPORTING,
            end_date=timezone.now() + relativedelta(days=1),
        )
        response = self.get_page(report)
        assert response.status_code == 403


class TestSkipReport(BaseViewTestCase):
    """Tests skipping report functionality"""

    base_view_name = "skip"
    url_name = "funds:projects:reports:{}"
    user_factory = StaffFactory

    def get_kwargs(self, instance):
        return {
            "pk": instance.pk,
        }

    def test_can_skip_report(self):
        """Tests report can be skipped"""
        report = ReportFactory(project__status=INVOICING_AND_REPORTING, past_due=True)
        response = self.post_page(report)
        assert response.status_code == 200
        report.refresh_from_db()
        assert report.skipped is True

    def test_can_unskip_report(self):
        """Tests skipped report can be restored"""
        report = ReportFactory(
            project__status=INVOICING_AND_REPORTING, skipped=True, past_due=True
        )
        response = self.post_page(report)
        assert response.status_code == 200
        report.refresh_from_db()
        assert report.skipped is False

    def test_cant_skip_current_report(self):
        """Tests current report cannot be skipped"""
        config = ReportConfigFactory(disable_reporting=False)
        report = ReportFactory(
            project=config.project,
            project__status=INVOICING_AND_REPORTING,
            end_date=timezone.now() + relativedelta(days=1),
        )
        response = self.post_page(report)
        assert response.status_code == 200
        report.refresh_from_db()
        assert report.skipped is False

    def test_cant_skip_submitted_report(self):
        """Tests submitted report cannot be skipped"""
        report = ReportFactory(
            project__status=INVOICING_AND_REPORTING, is_submitted=True
        )
        response = self.post_page(report, data={})
        assert response.status_code == 200
        report.refresh_from_db()
        assert report.skipped is False

    def test_can_skip_draft_report(self):
        """Tests draft report can be skipped"""
        report = ReportFactory(
            project__status=INVOICING_AND_REPORTING, is_draft=True, past_due=True
        )
        response = self.post_page(report)
        assert response.status_code == 200
        report.refresh_from_db()
        assert report.skipped is True


class TestReportListView(BaseViewTestCase):
    base_view_name = "submitted"
    url_name = "funds:projects:reports:{}"
    user_factory = StaffFactory

    def test_staff_can_access(self):
        ReportFactory(is_submitted=True)
        response = self.get_page()
        assert response.status_code == 200

    def test_applicant_cant_access(self):
        self.client.force_login(ApplicantFactory())
        response = self.client.get(reverse("funds:projects:reports:submitted"))
        assert response.status_code == 403


class TestReportingView(BaseViewTestCase):
    base_view_name = "all"
    url_name = "funds:projects:reports:{}"
    user_factory = StaffFactory

    def test_staff_can_access(self):
        ProjectFactory(status=INVOICING_AND_REPORTING)
        response = self.get_page()
        assert response.status_code == 200

    def test_applicant_cant_access(self):
        self.client.force_login(ApplicantFactory())
        response = self.client.get(reverse("funds:projects:reports:all"))
        assert response.status_code == 403


class TestReportFrequencyUpdate(BaseViewTestCase):
    base_view_name = "report_frequency_update"
    url_name = "funds:projects:{}"
    user_factory = StaffFactory

    def get_kwargs(self, instance):
        return {"pk": instance.submission.id}

    def test_staff_can_access(self):
        project = ProjectFactory(status=INVOICING_AND_REPORTING)
        ReportConfigFactory(project=project)
        response = self.get_page(project)
        assert response.status_code == 200

    def test_applicant_cant_access(self):
        project = ProjectFactory(status=INVOICING_AND_REPORTING)
        ReportConfigFactory(project=project)
        self.client.force_login(ApplicantFactory())
        url = reverse(
            "funds:projects:report_frequency_update",
            kwargs={"pk": project.submission.id},
        )
        response = self.client.get(url)
        assert response.status_code == 403
