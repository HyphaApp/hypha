"""Access control tests for the object "Status & Activity" partials.

These partials render comment bodies, so they must be scoped to the project in
the URL and gated on the requesting user's access to that project.
"""

from django.test import TestCase
from django.urls import reverse

from hypha.apply.activity import services
from hypha.apply.activity.models import COMMENT
from hypha.apply.activity.tests.factories import ActivityFactory
from hypha.apply.projects.reports.tests.factories import ReportFactory
from hypha.apply.users.tests.factories import (
    ApplicantFactory,
    ContractingFactory,
    FinanceFactory,
    StaffFactory,
)

from ..models.project import INVOICING_AND_REPORTING
from .factories import (
    InvoiceFactory,
    ProjectFactory,
    ProjectFormPointerFactory,
    ProjectSOWFactory,
)


class BaseObjectActivityPartialTestCase(TestCase):
    """Builds one project with every commentable object hanging off it"""

    def setUp(self):
        self.vendor = ApplicantFactory()
        self.project = ProjectFactory(status=INVOICING_AND_REPORTING, user=self.vendor)
        self.other_project = ProjectFactory(status=INVOICING_AND_REPORTING)

        self.invoice = InvoiceFactory(project=self.project)
        self.report = ReportFactory(project=self.project, is_submitted=True)
        self.sow = ProjectSOWFactory(project=self.project)
        self.pfp = ProjectFormPointerFactory(project=self.project)

    def urls(self, project=None):
        project = project or self.project
        return {
            "invoice": reverse(
                "apply:projects:partial-invoice-status",
                kwargs={"pk": project.pk, "invoice_pk": self.invoice.pk},
            ),
            "report": reverse(
                "apply:projects:partial-report-status",
                kwargs={"pk": project.pk, "report_pk": self.report.pk},
            ),
            "sow": reverse(
                "apply:projects:partial-sow-status",
                kwargs={"pk": project.pk, "sow_pk": self.sow.pk},
            ),
            "pf": reverse(
                "apply:projects:partial-pf-status",
                kwargs={"pk": project.pk, "pfp_pk": self.pfp.pk},
            ),
        }


class TestObjectActivityPartialAccess(BaseObjectActivityPartialTestCase):
    def test_staff_can_view_all(self):
        self.client.force_login(StaffFactory())
        for name, url in self.urls().items():
            with self.subTest(name):
                self.assertEqual(self.client.get(url, secure=True).status_code, 200)

    def test_finance_can_view_all(self):
        self.client.force_login(FinanceFactory())
        for name, url in self.urls().items():
            with self.subTest(name):
                self.assertEqual(self.client.get(url, secure=True).status_code, 200)

    def test_contracting_can_view_project_forms_only(self):
        """Contracting has project access, but not report or invoice access

        `view_report` and `invoice_access` exclude contracting, exactly as
        `ReportDetailView` and `InvoiceAccessMixin` do on the pages themselves.
        """
        self.client.force_login(ContractingFactory())
        urls = self.urls()
        for name in ["report", "invoice"]:
            with self.subTest(name):
                self.assertEqual(
                    self.client.get(urls.pop(name), secure=True).status_code, 403
                )
        for name, url in urls.items():
            with self.subTest(name):
                self.assertEqual(self.client.get(url, secure=True).status_code, 200)

    def test_project_vendor_can_view_all(self):
        self.client.force_login(self.vendor)
        for name, url in self.urls().items():
            with self.subTest(name):
                self.assertEqual(self.client.get(url, secure=True).status_code, 200)

    def test_unrelated_applicant_is_denied(self):
        """The core regression: an applicant on another project must not read these"""
        self.client.force_login(ApplicantFactory())
        for name, url in self.urls().items():
            with self.subTest(name):
                self.assertEqual(self.client.get(url, secure=True).status_code, 403)

    def test_anonymous_is_redirected_to_login(self):
        for name, url in self.urls().items():
            with self.subTest(name):
                self.assertEqual(self.client.get(url, secure=True).status_code, 302)

    def test_objects_are_scoped_to_the_project_in_the_url(self):
        """A valid object id under the wrong project pk must 404, not resolve"""
        self.client.force_login(StaffFactory())
        for name, url in self.urls(project=self.other_project).items():
            with self.subTest(name):
                self.assertEqual(self.client.get(url, secure=True).status_code, 404)

    def test_comment_body_not_leaked_to_unrelated_applicant(self):
        comment = ActivityFactory(
            source=self.project.submission,
            related_object=self.invoice,
            user=StaffFactory(),
            message="a confidential internal note",
        )
        self.client.force_login(ApplicantFactory())
        response = self.client.get(self.urls()["invoice"], secure=True)
        self.assertEqual(response.status_code, 403)
        self.assertNotContains(response, comment.message, status_code=403)

    def test_post_is_not_allowed(self):
        self.client.force_login(StaffFactory())
        for name, url in self.urls().items():
            with self.subTest(name):
                self.assertEqual(self.client.post(url, secure=True).status_code, 405)


class TestObjectActivityPartialContent(BaseObjectActivityPartialTestCase):
    def test_edited_comment_is_only_rendered_once(self):
        """Superseded revisions (`current=False`) must not be listed"""
        staff = StaffFactory()
        comment = ActivityFactory(
            source=self.project.submission,
            related_object=self.invoice,
            user=staff,
            type=COMMENT,
            message="the original message",
        )
        # Clones the old revision as `current=False`, keeping the relation.
        services.edit_comment(comment, "the edited message")

        self.client.force_login(staff)
        response = self.client.get(self.urls()["invoice"], secure=True)

        self.assertEqual(len(response.context["activities"]), 1)
        self.assertNotContains(response, "the original message")
