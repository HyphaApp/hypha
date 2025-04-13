from django.test import TestCase
from django.urls import reverse

from hypha.apply.projects.tests.factories import ReportFactory


class TestReportListPage(TestCase):
    def test_staff_can_access_report_list_page(self):
        """Test that staff users can access the report list page"""
        from hypha.apply.users.tests.factories import StaffFactory

        ReportFactory(is_submitted=True)

        self.client.force_login(StaffFactory())
        url = reverse("funds:projects:reports:submitted")
        response = self.client.get(url, follow=True)
        assert response.status_code == 200

    def test_applicants_cannot_access_report_list_page(self):
        """Test that applicant users cannot access the report list page"""
        from hypha.apply.users.tests.factories import ApplicantFactory

        ReportFactory(is_submitted=True)

        self.client.force_login(ApplicantFactory())
        url = reverse("funds:projects:reports:submitted")
        response = self.client.get(url, follow=True)
        assert response.status_code == 403


class TestReportingPage(TestCase):
    def test_staff_can_access_reporting_page(self):
        """Test that staff users can access the reporting page"""
        from hypha.apply.projects.models.project import INVOICING_AND_REPORTING
        from hypha.apply.projects.tests.factories import ProjectFactory
        from hypha.apply.users.tests.factories import StaffFactory

        ProjectFactory(status=INVOICING_AND_REPORTING)

        self.client.force_login(StaffFactory())
        url = reverse("funds:projects:reports:all")
        response = self.client.get(url, follow=True)
        assert response.status_code == 200

    def test_applicants_cannot_access_reporting_page(self):
        """Test that applicant users cannot access the reporting page"""
        from hypha.apply.users.tests.factories import ApplicantFactory

        self.client.force_login(ApplicantFactory())
        url = reverse("funds:projects:reports:all")
        response = self.client.get(url, follow=True)
        assert response.status_code == 403
