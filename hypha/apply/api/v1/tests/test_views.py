from django.test import TestCase, override_settings
from django.urls import reverse_lazy
from rest_framework.exceptions import ErrorDetail

from hypha.apply.activity.models import ALL, APPLICANT, Activity
from hypha.apply.activity.tests.factories import CommentFactory
from hypha.apply.projects.models.payment import (
    APPROVED_BY_FINANCE,
    APPROVED_BY_FINANCE_2,
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
    Finance2Factory,
    FinanceFactory,
    StaffFactory,
    UserFactory,
)


class TestCommentEdit(TestCase):
    def post_to_edit(self, comment_pk, message="my message"):
        return self.client.post(
            reverse_lazy("api:v1:comments-edit", kwargs={"pk": comment_pk}),
            secure=True,
            data={"message": message},
        )

    def test_cant_edit_if_not_author(self):
        comment = CommentFactory()
        response = self.post_to_edit(comment.pk)
        self.assertEqual(response.status_code, 403)

    def test_edit_updates_correctly(self):
        user = StaffFactory()
        comment = CommentFactory(user=user)
        self.client.force_login(user)

        new_message = "hi there"

        response = self.post_to_edit(comment.pk, new_message)

        self.assertEqual(response.status_code, 200, response.json())
        self.assertEqual(Activity.objects.count(), 2)

        comment.refresh_from_db()

        time = comment.timestamp.timestamp() * 1000

        self.assertEqual(time, response.json()["timestamp"])
        self.assertFalse(comment.current)
        self.assertEqual(response.json()["message"], new_message)

    def test_incorrect_id_denied(self):
        response = self.post_to_edit(10000)
        self.assertEqual(response.status_code, 403, response.json())

    def test_does_nothing_if_same_message_and_visibility(self):
        user = UserFactory()
        comment = CommentFactory(user=user)
        self.client.force_login(user)

        self.client.post(
            reverse_lazy("api:v1:comments-edit", kwargs={"pk": comment.pk}),
            secure=True,
            data={
                "message": comment.message,
                "visibility": comment.visibility,
            },
        )

        self.assertEqual(Activity.objects.count(), 1)

    def test_staff_can_change_visibility(self):
        user = StaffFactory()
        comment = CommentFactory(user=user, visibility=APPLICANT)
        self.client.force_login(user)

        response = self.client.post(
            reverse_lazy("api:v1:comments-edit", kwargs={"pk": comment.pk}),
            secure=True,
            data={
                "message": "the new message",
                "visibility": ALL,
            },
        )

        self.assertEqual(response.status_code, 200, response.json())
        self.assertEqual(response.json()["visibility"], ALL)

    def test_out_of_order_does_nothing(self):
        user = ApplicantFactory()  # any role assigned user
        comment = CommentFactory(user=user)
        self.client.force_login(user)

        new_message = "hi there"
        newer_message = "hello there"

        response_one = self.post_to_edit(comment.pk, new_message)
        response_two = self.post_to_edit(comment.pk, newer_message)

        self.assertEqual(response_one.status_code, 200, response_one.json())
        self.assertEqual(response_two.status_code, 404, response_two.json())
        self.assertEqual(Activity.objects.count(), 2)


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

    @override_settings(INVOICE_EXTENDED_WORKFLOW=True)
    def test_finance2_can_add_deliverables(self):
        user = Finance2Factory()
        project = ProjectFactory()
        invoice = InvoiceFactory(project=project, status=APPROVED_BY_FINANCE)
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

    @override_settings(INVOICE_EXTENDED_WORKFLOW=True)
    def test_finance2_can_remove_deliverables(self):
        user = Finance2Factory()
        project = ProjectFactory()
        invoice = InvoiceFactory(project=project, status=APPROVED_BY_FINANCE)
        deliverable = DeliverableFactory(project=project)
        invoice_deliverable = InvoiceDeliverableFactory(deliverable=deliverable)
        invoice.deliverables.add(invoice_deliverable)
        self.client.force_login(user)

        response = self.delete_to_remove(project.id, invoice.id, invoice_deliverable.id)
        self.assertEqual(response.status_code, 200)

    def test_deliverables_cant_removed_after_finance2_approval(self):
        project = ProjectFactory()
        invoice = InvoiceFactory(project=project, status=APPROVED_BY_FINANCE_2)
        deliverable = DeliverableFactory(project=project)
        invoice_deliverable = InvoiceDeliverableFactory(deliverable=deliverable)
        invoice.deliverables.add(invoice_deliverable)

        finance1 = FinanceFactory()
        finance2 = Finance2Factory()
        staff = StaffFactory()
        for user in [staff, finance1, finance2]:
            self.client.force_login(user)
            response = self.delete_to_remove(
                project.id, invoice.id, invoice_deliverable.id
            )
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
