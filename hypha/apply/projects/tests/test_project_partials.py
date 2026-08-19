"""Access control tests for the project detail HTMX partials.

Every partial under `views/project_partials.py` takes a project pk from the URL,
so each must confirm the requesting user may see that project - and the
invoice-scoped ones must confirm the invoice belongs to it.
"""

from django.test import TestCase
from django.urls import reverse

from hypha.apply.users.tests.factories import (
    ApplicantFactory,
    ContractingFactory,
    FinanceFactory,
    StaffFactory,
)

from ..models.project import INVOICING_AND_REPORTING
from .factories import InvoiceFactory, ProjectFactory


class BaseProjectPartialTestCase(TestCase):
    def setUp(self):
        self.vendor = ApplicantFactory()
        self.project = ProjectFactory(status=INVOICING_AND_REPORTING, user=self.vendor)
        self.invoice = InvoiceFactory(project=self.project)

    def project_urls(self, project=None):
        project = project or self.project
        return {
            name: reverse(f"apply:projects:{name}", kwargs={"pk": project.pk})
            for name in [
                "project_lead",
                "project_title",
                "project_information",
                "supporting_documents",
                "contract_documents",
                "partial-invoices-status",
                "partial-rejected-invoices-status",
            ]
        }

    def invoice_urls(self, project=None):
        project = project or self.project
        return {
            name: reverse(
                f"apply:projects:{name}",
                kwargs={"pk": project.pk, "invoice_pk": self.invoice.pk},
            )
            for name in [
                "partial-invoice-detail-actions",
                "partial-invoice-tags",
            ]
        }


class TestProjectPartialAccess(BaseProjectPartialTestCase):
    def test_staff_can_view_everything(self):
        self.client.force_login(StaffFactory())
        for name, url in {**self.project_urls(), **self.invoice_urls()}.items():
            with self.subTest(name):
                self.assertEqual(self.client.get(url, secure=True).status_code, 200)

    def test_project_vendor_can_view_everything(self):
        self.client.force_login(self.vendor)
        for name, url in {**self.project_urls(), **self.invoice_urls()}.items():
            with self.subTest(name):
                self.assertEqual(self.client.get(url, secure=True).status_code, 200)

    def test_unrelated_applicant_is_denied(self):
        self.client.force_login(ApplicantFactory())
        for name, url in {**self.project_urls(), **self.invoice_urls()}.items():
            with self.subTest(name):
                self.assertEqual(self.client.get(url, secure=True).status_code, 403)

    def test_anonymous_is_redirected(self):
        for name, url in {**self.project_urls(), **self.invoice_urls()}.items():
            with self.subTest(name):
                self.assertEqual(self.client.get(url, secure=True).status_code, 302)

    def test_contracting_has_project_access_but_not_invoice_access(self):
        self.client.force_login(ContractingFactory())
        for name, url in self.project_urls().items():
            with self.subTest(name):
                self.assertEqual(self.client.get(url, secure=True).status_code, 200)
        for name, url in self.invoice_urls().items():
            with self.subTest(name):
                self.assertEqual(self.client.get(url, secure=True).status_code, 403)

    def test_finance_can_view_everything(self):
        self.client.force_login(FinanceFactory())
        for name, url in {**self.project_urls(), **self.invoice_urls()}.items():
            with self.subTest(name):
                self.assertEqual(self.client.get(url, secure=True).status_code, 200)

    def test_invoice_is_scoped_to_the_project_in_the_url(self):
        other_project = ProjectFactory(status=INVOICING_AND_REPORTING)
        self.client.force_login(StaffFactory())
        for name, url in self.invoice_urls(project=other_project).items():
            with self.subTest(name):
                self.assertEqual(self.client.get(url, secure=True).status_code, 404)

    def test_post_is_not_allowed(self):
        self.client.force_login(StaffFactory())
        for name, url in {**self.project_urls(), **self.invoice_urls()}.items():
            with self.subTest(name):
                self.assertEqual(self.client.post(url, secure=True).status_code, 405)
