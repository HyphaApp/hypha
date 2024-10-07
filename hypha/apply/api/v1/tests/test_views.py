from django.test import TestCase
from django.urls import reverse_lazy
from rest_framework.exceptions import ErrorDetail

from hypha.apply.projects.models.payment import (
    APPROVED_BY_FINANCE,
    APPROVED_BY_STAFF,
    SUBMITTED,
)
from hypha.apply.projects.tests.factories import (
    DeliverableFactory,
    InvoiceDeliverableFactory,
    InvoiceFactory,
    ProjectFactory,
)
from hypha.apply.users.tests.factories import (
    ApplicantFactory,
    FinanceFactory,
    StaffFactory,
)


class TestInvoiceDeliverableViewset(TestCase):
    def post_to_add(self, project_id, invoice_id, deliverable_id, quantity=1):
        return self.client.post(
            reverse_lazy(
                "api:v1:set-deliverables",
                kwargs={"project_pk": project_id, "invoice_pk": invoice_id},
            ),
            secure=True,
            data={"id": deliverable_id, "quantity": quantity},
        )

    def delete_to_remove(self, project_id, invoice_id, deliverable_id):
        return self.client.delete(
            reverse_lazy(
                "api:v1:remove-deliverables",
                kwargs={
                    "project_pk": project_id,
                    "invoice_pk": invoice_id,
                    "pk": deliverable_id,
                },
            ),
            secure=True,
        )

    def test_cant_add_or_remove_wihtout_login(self):
        project = ProjectFactory()
        invoice = InvoiceFactory(project=project)
        deliverable = DeliverableFactory(project=project)
        invoice_deliverable = InvoiceDeliverableFactory(deliverable=deliverable)

        response = self.post_to_add(project.id, invoice.id, deliverable.id)
        self.assertEqual(response.status_code, 403)

        response = self.delete_to_remove(project.id, invoice.id, invoice_deliverable.id)
        self.assertEqual(response.status_code, 403)

    def test_applicant_cant_add_deliverables(self):
        user = ApplicantFactory()
        project = ProjectFactory()
        invoice = InvoiceFactory(project=project)
        deliverable = DeliverableFactory(project=project)
        self.client.force_login(user)

        response = self.post_to_add(project.id, invoice.id, deliverable.id)
        self.assertEqual(response.status_code, 403)

    def test_staff_can_add_deliverables(self):
        user = StaffFactory()
        project = ProjectFactory()
        invoice = InvoiceFactory(project=project, status=SUBMITTED)
        deliverable = DeliverableFactory(project=project)
        self.client.force_login(user)

        response = self.post_to_add(project.id, invoice.id, deliverable.id)
        self.assertEqual(response.status_code, 201)

    def test_finance1_can_add_deliverables(self):
        user = FinanceFactory()
        project = ProjectFactory()
        invoice = InvoiceFactory(project=project, status=APPROVED_BY_STAFF)
        deliverable = DeliverableFactory(project=project)
        self.client.force_login(user)

        response = self.post_to_add(project.id, invoice.id, deliverable.id)
        self.assertEqual(response.status_code, 201)

    def test_applicant_cant_remove_deliverables(self):
        user = ApplicantFactory()
        project = ProjectFactory()
        invoice = InvoiceFactory(project=project)
        deliverable = DeliverableFactory(project=project)
        invoice_deliverable = InvoiceDeliverableFactory(deliverable=deliverable)
        invoice.deliverables.add(invoice_deliverable)
        self.client.force_login(user)

        response = self.delete_to_remove(project.id, invoice.id, invoice_deliverable.id)
        self.assertEqual(response.status_code, 403)

    def test_staff_can_remove_deliverables(self):
        user = StaffFactory()
        project = ProjectFactory()
        invoice = InvoiceFactory(project=project, status=SUBMITTED)
        deliverable = DeliverableFactory(project=project)
        invoice_deliverable = InvoiceDeliverableFactory(deliverable=deliverable)
        invoice.deliverables.add(invoice_deliverable)
        self.client.force_login(user)

        response = self.delete_to_remove(project.id, invoice.id, invoice_deliverable.id)
        self.assertEqual(response.status_code, 200)

    def test_staff_cant_remove_deliverables_after_staff_approval(self):
        user = StaffFactory()
        project = ProjectFactory()
        invoice = InvoiceFactory(project=project, status=APPROVED_BY_STAFF)
        deliverable = DeliverableFactory(project=project)
        invoice_deliverable = InvoiceDeliverableFactory(deliverable=deliverable)
        invoice.deliverables.add(invoice_deliverable)
        self.client.force_login(user)

        response = self.delete_to_remove(project.id, invoice.id, invoice_deliverable.id)
        self.assertEqual(response.status_code, 403)

    def test_finance1_can_remove_deliverables(self):
        user = FinanceFactory()
        project = ProjectFactory()
        invoice = InvoiceFactory(project=project, status=APPROVED_BY_STAFF)
        deliverable = DeliverableFactory(project=project)
        invoice_deliverable = InvoiceDeliverableFactory(deliverable=deliverable)
        invoice.deliverables.add(invoice_deliverable)
        self.client.force_login(user)

        response = self.delete_to_remove(project.id, invoice.id, invoice_deliverable.id)
        self.assertEqual(response.status_code, 200)

    def test_finance1_cant_remove_deliverables_after_finance1_approval(self):
        user = FinanceFactory()
        project = ProjectFactory()
        invoice = InvoiceFactory(project=project, status=APPROVED_BY_FINANCE)
        deliverable = DeliverableFactory(project=project)
        invoice_deliverable = InvoiceDeliverableFactory(deliverable=deliverable)
        invoice.deliverables.add(invoice_deliverable)
        self.client.force_login(user)

        response = self.delete_to_remove(project.id, invoice.id, invoice_deliverable.id)
        self.assertEqual(response.status_code, 403)

    def test_deliverable_dont_exists_in_project_deliverables(self):
        user = StaffFactory()
        project = ProjectFactory()
        invoice = InvoiceFactory(project=project, status=SUBMITTED)
        deliverable = DeliverableFactory()
        self.client.force_login(user)

        response = self.post_to_add(project.id, invoice.id, deliverable.id)
        self.assertEqual(response.status_code, 400)
        error_message = {"detail": ErrorDetail(string="Not Found", code="invalid")}
        self.assertEqual(response.data, error_message)

    def test_deliverable_already_exists_in_invoice(self):
        user = StaffFactory()
        project = ProjectFactory()
        invoice = InvoiceFactory(project=project, status=SUBMITTED)
        deliverable = DeliverableFactory(project=project)
        invoice_deliverable = InvoiceDeliverableFactory(deliverable=deliverable)
        invoice.deliverables.add(invoice_deliverable)
        self.client.force_login(user)

        response = self.post_to_add(project.id, invoice.id, deliverable.id)
        self.assertEqual(response.status_code, 400)
        error_message = {
            "detail": ErrorDetail(
                string="Invoice Already has this deliverable", code="invalid"
            )
        }
        self.assertEqual(response.data, error_message)

    def test_deliverable_available_gte_quantity(self):
        user = StaffFactory()
        project = ProjectFactory()
        invoice = InvoiceFactory(project=project, status=SUBMITTED)
        deliverable = DeliverableFactory(project=project)
        self.client.force_login(user)

        response = self.post_to_add(project.id, invoice.id, deliverable.id, quantity=3)
        self.assertEqual(response.status_code, 400)
        error_message = {
            "detail": ErrorDetail(
                string="Required quantity is more than available", code="invalid"
            )
        }
        self.assertEqual(response.data, error_message)
