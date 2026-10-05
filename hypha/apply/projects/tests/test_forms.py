import datetime
import json
from decimal import Decimal
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from hypha.apply.users.tests.factories import (
    FinanceFactory,
    StaffFactory,
    UserFactory,
)
from hypha.home.factories import ApplySiteFactory

from ..files import get_files
from ..forms.invoice import (
    ChangeInvoiceStatusForm,
    CreateInvoiceForm,
    EditInvoiceForm,
    SelectDocumentForm,
    filter_request_choices,
)
from ..forms.project import (
    ChangePAFStatusForm,
    CreateContractForm,
    ProjectCreateForm,
    StaffUploadContractForm,
    UploadContractForm,
)
from ..models.invoice import (
    APPROVED_BY_FINANCE,
    APPROVED_BY_STAFF,
    CHANGES_REQUESTED_BY_FINANCE,
    CHANGES_REQUESTED_BY_STAFF,
    DECLINED,
    RESUBMITTED,
    SUBMITTED,
    invoice_status_user_choices,
)
from ..models.project import APPROVE, ProjectSettings
from .factories import (
    DocumentCategoryFactory,
    InvoiceFactory,
    PAFReviewerRoleFactory,
    ProjectFactory,
    SupportingDocumentFactory,
)


class TestProjectCreateForm(TestCase):
    def test_allows_submission_that_already_has_a_project(self):
        from hypha.apply.funds.tests.factories import ApplicationSubmissionFactory

        from ..forms.utils import get_project_default_status

        staff = StaffFactory()
        submission = ApplicationSubmissionFactory()
        ProjectFactory(submission=submission)

        form = ProjectCreateForm(
            instance=submission,
            data={
                "submission": submission.id,
                "title": "Second bucket",
                "project_lead": staff.id,
                "project_initial_status": get_project_default_status()[0],
                "project_end": datetime.date.today(),
            },
        )

        self.assertTrue(form.is_valid(), form.errors)
        project = form.save()
        self.assertEqual(project.title, "Second bucket")
        self.assertEqual(submission.projects.count(), 2)


class TestChangeInvoiceStatusFormForm(TestCase):
    def test_staff_choices_with_submitted_status(self):
        invoice = InvoiceFactory(status=SUBMITTED)
        user = StaffFactory()
        form = ChangeInvoiceStatusForm(instance=invoice, user=user)

        expected = set(
            filter_request_choices(
                [CHANGES_REQUESTED_BY_STAFF, APPROVED_BY_STAFF, DECLINED],
                invoice_status_user_choices(user),
            )
        )
        actual = set(form.fields["status"].choices)
        self.assertEqual(expected, actual)

    def test_finance1_choices_with_submitted_status(self):
        invoice = InvoiceFactory(status=SUBMITTED)
        user = FinanceFactory()
        form = ChangeInvoiceStatusForm(instance=invoice, user=user)

        expected = set(
            filter_request_choices(
                [CHANGES_REQUESTED_BY_STAFF, APPROVED_BY_STAFF, DECLINED],
                invoice_status_user_choices(user),
            )
        )
        actual = set(form.fields["status"].choices)
        self.assertEqual(expected, actual)

    def test_staff_choices_with_resubmitted_status(self):
        invoice = InvoiceFactory(status=RESUBMITTED)
        user = StaffFactory()
        form = ChangeInvoiceStatusForm(instance=invoice, user=user)

        expected = set(
            filter_request_choices(
                [CHANGES_REQUESTED_BY_STAFF, APPROVED_BY_STAFF, DECLINED],
                invoice_status_user_choices(user),
            )
        )
        actual = set(form.fields["status"].choices)
        self.assertEqual(expected, actual)

    def test_finance1_choices_with_resubmitted_status(self):
        invoice = InvoiceFactory(status=RESUBMITTED)
        user = FinanceFactory()
        form = ChangeInvoiceStatusForm(instance=invoice, user=user)

        expected = set(
            filter_request_choices(
                [CHANGES_REQUESTED_BY_STAFF, APPROVED_BY_STAFF, DECLINED],
                invoice_status_user_choices(user),
            )
        )
        actual = set(form.fields["status"].choices)
        self.assertEqual(expected, actual)

    def test_staff_choices_with_changes_requested_by_staff_status(self):
        invoice = InvoiceFactory(status=CHANGES_REQUESTED_BY_STAFF)
        user = StaffFactory()
        form = ChangeInvoiceStatusForm(instance=invoice, user=user)

        expected = set(
            filter_request_choices([DECLINED], invoice_status_user_choices(user))
        )
        actual = set(form.fields["status"].choices)
        self.assertEqual(expected, actual)

    def test_finance1_choices_with_changes_requested_by_staff_status(self):
        invoice = InvoiceFactory(status=CHANGES_REQUESTED_BY_STAFF)
        user = FinanceFactory()
        form = ChangeInvoiceStatusForm(instance=invoice, user=user)

        expected = set(
            filter_request_choices([DECLINED], invoice_status_user_choices(user))
        )
        actual = set(form.fields["status"].choices)
        self.assertEqual(expected, actual)

    def test_staff_choices_with_approved_by_staff_status(self):
        invoice = InvoiceFactory(status=APPROVED_BY_STAFF)
        user = StaffFactory()
        form = ChangeInvoiceStatusForm(instance=invoice, user=user)

        expected = set(
            filter_request_choices(
                [CHANGES_REQUESTED_BY_FINANCE, APPROVED_BY_FINANCE],
                invoice_status_user_choices(user),
            )
        )
        actual = set(form.fields["status"].choices)
        self.assertEqual(expected, actual)

    def test_finance1_choices_with_approved_by_staff_status(self):
        invoice = InvoiceFactory(status=APPROVED_BY_STAFF)
        user = FinanceFactory()
        form = ChangeInvoiceStatusForm(instance=invoice, user=user)

        expected = set(
            filter_request_choices(
                [CHANGES_REQUESTED_BY_FINANCE, APPROVED_BY_FINANCE],
                invoice_status_user_choices(user),
            )
        )
        actual = set(form.fields["status"].choices)
        self.assertEqual(expected, actual)

    def test_staff_choices_with_changes_requested_by_finance1_status(self):
        invoice = InvoiceFactory(status=CHANGES_REQUESTED_BY_FINANCE)
        user = StaffFactory()
        form = ChangeInvoiceStatusForm(instance=invoice, user=user)

        expected = set(
            filter_request_choices(
                [CHANGES_REQUESTED_BY_STAFF, DECLINED],
                invoice_status_user_choices(user),
            )
        )
        actual = set(form.fields["status"].choices)
        self.assertEqual(expected, actual)

    def test_finance1_choices_with_changes_requested_by_finance1_status(self):
        invoice = InvoiceFactory(status=CHANGES_REQUESTED_BY_FINANCE)
        user = FinanceFactory()
        form = ChangeInvoiceStatusForm(instance=invoice, user=user)

        expected = set(
            filter_request_choices(
                [CHANGES_REQUESTED_BY_STAFF, DECLINED],
                invoice_status_user_choices(user),
            )
        )
        actual = set(form.fields["status"].choices)
        self.assertEqual(expected, actual)


class TestChangePAFStatusForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        apply_site = ApplySiteFactory()
        cls.project_setting, _ = ProjectSettings.objects.get_or_create(
            site_id=apply_site.id
        )
        cls.project_setting.use_settings = True
        cls.project_setting.save()
        cls.role = PAFReviewerRoleFactory(page=cls.project_setting)

    def test_paf_status_is_required(self):
        project = ProjectFactory(in_approval=True)
        form = ChangePAFStatusForm(data={"comment": "comment"}, instance=project)
        self.assertFalse(form.is_valid())
        self.assertIn("paf_status", form.errors.keys())

    def test_comment_is_not_required(self):
        project = ProjectFactory(in_approval=True)
        form = ChangePAFStatusForm(data={"paf_status": APPROVE}, instance=project)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.errors, {})


class TestCreateInvoiceForm(TestCase):
    def test_adding_invoice(self):
        data = {
            "invoice_number": "00INV_NUM",
            "invoice_amount": "10",
            "invoice_date": datetime.date.today(),
            "paid_value": "10",
            "comment": "test comment",
        }

        document = SimpleUploadedFile(
            "test_invoice.pdf", BytesIO(b"somebinarydata").read()
        )
        supporting_documents = [
            SimpleUploadedFile("test_invoice.pdf", BytesIO(b"somebinarydata").read())
        ]
        files = {"document": document, "supporting_documents": supporting_documents}

        form = CreateInvoiceForm(data=data, files=files)
        self.assertTrue(form.is_valid(), msg=form.errors)

        form.instance.by = UserFactory()
        form.instance.project = ProjectFactory()
        invoice = form.save()

        self.assertEqual(invoice.status, SUBMITTED)
        self.assertIsNotNone(invoice.document)
        self.assertEqual(invoice.supporting_documents.count(), 1)

    def test_supporting_documents_not_required(self):
        data = {
            "invoice_number": "00INV_NUM",
            "invoice_amount": "10",
            "invoice_date": datetime.date.today(),
            "paid_value": "10",
            "comment": "test comment",
        }

        document = SimpleUploadedFile(
            "test_invoice.pdf", BytesIO(b"somebinarydata").read()
        )
        files = {
            "document": document,
        }

        form = CreateInvoiceForm(data=data, files=files)
        self.assertTrue(form.is_valid(), msg=form.errors)

        form.instance.by = UserFactory()
        form.instance.project = ProjectFactory()
        invoice = form.save()

        self.assertEqual(invoice.supporting_documents.count(), 0)


class TestEditInvoiceForm(TestCase):
    def test_remove_existing_supporting_document(self):
        invoice = InvoiceFactory()
        SupportingDocumentFactory(invoice=invoice, document=invoice.document)
        self.assertTrue(invoice.supporting_documents.exists())

        form = EditInvoiceForm(
            data={
                "invoice_number": invoice.invoice_number,
                "invoice_amount": invoice.invoice_amount,
                "invoice_date": invoice.invoice_date,
                "document": invoice.document,
                "supporting_documents-uploads": "[]",
            },
            files={
                "supporting_documents": [],
            },
            instance=invoice,
        )
        self.assertTrue(form.is_valid())

        form.save()
        self.assertFalse(invoice.supporting_documents.exists())

    def test_keep_existing_supporting_document(self):
        invoice = InvoiceFactory()
        supporting_document = SupportingDocumentFactory(invoice=invoice)
        self.assertEqual(invoice.supporting_documents.count(), 1)

        form = EditInvoiceForm(
            data={
                "invoice_number": invoice.invoice_number,
                "invoice_amount": invoice.invoice_amount,
                "invoice_date": invoice.invoice_date,
                "document": invoice.document,
                "supporting_documents-uploads": json.dumps(
                    [
                        {
                            "name": supporting_document.document.name,
                            "size": supporting_document.document.size,
                            "type": "existing",
                        }
                    ]
                ),
            },
            instance=invoice,
        )
        self.assertTrue(form.is_valid())

        invoice = form.save()
        self.assertEqual(invoice.supporting_documents.count(), 1)

    def test_add_new_supporting_document(self):
        invoice = InvoiceFactory()
        self.assertEqual(invoice.supporting_documents.count(), 0)

        supporting_document = [
            SimpleUploadedFile("test_invoice.pdf", BytesIO(b"somebinarydata").read())
        ]
        form = EditInvoiceForm(
            data={
                "invoice_number": invoice.invoice_number,
                "invoice_amount": invoice.invoice_amount,
                "invoice_date": invoice.invoice_date,
                "document": invoice.document,
                "supporting_documents-uploads": "[]",
            },
            files={
                "supporting_documents": supporting_document,
            },
            instance=invoice,
        )
        self.assertTrue(form.is_valid())

        invoice = form.save()
        self.assertEqual(invoice.supporting_documents.count(), 1)


class TestSelectDocumentForm(TestCase):
    def test_copying_files(self):
        category = DocumentCategoryFactory()
        project = ProjectFactory(submission__with_files=True)

        self.assertEqual(project.packet_files.count(), 0)

        files = list(get_files(project))
        self.assertEqual(len(files), 4)

        url = files[3].url

        form = SelectDocumentForm(
            files,
            data={"category": category.id, "document": url},
        )
        self.assertTrue(form.is_valid(), form.errors)

        form.instance.project = project
        form.save()

        packet_files = project.packet_files.order_by("id")
        self.assertEqual(len(packet_files), 1)

        self.assertEqual(packet_files.first().document.read(), files[3].read())


class TestStaffContractUploadForm(TestCase):
    mock_file = SimpleUploadedFile(
        "test_contract.pdf", BytesIO(b"somebinarydata").read()
    )

    def test_staff_can_upload_unsigned(self):
        form = StaffUploadContractForm(data={}, files={"file": self.mock_file})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertFalse(form.cleaned_data.get("signed_by_applicant"))

    def test_staff_can_upload_signed(self):
        form = StaffUploadContractForm(
            data={"signed_by_applicant": True}, files={"file": self.mock_file}
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertTrue(form.cleaned_data.get("signed_by_applicant"))


@override_settings(PROJECTS_PAYMENTS_FLOW="DISBURSEMENTS")
class TestContractUploadForm(TestCase):
    mock_file = SimpleUploadedFile(
        "test_contract.pdf", BytesIO(b"somebinarydata").read()
    )

    def test_applicant_cant_upload_unsigned(self):
        form = UploadContractForm(data={}, files={"file": self.mock_file})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertIsNone(form.cleaned_data.get("signed_by_applicant"))

    def test_applicant_can_upload_signed(self):
        form = UploadContractForm(
            data={"signed_by_applicant": True}, files={"file": self.mock_file}
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertIsNone(form.cleaned_data.get("signed_by_applicant"))

    def test_can_set_amounts_to_wide_precision_with_no_currency(self):
        form = UploadContractForm(
            data={
                "amount_approved": "43.0000000000043",
                "amount_requested": "17.0000000000000000017",
            },
            files={"file": self.mock_file},
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(
            form.cleaned_data.get("amount_approved"), Decimal("43.0000000000043")
        )
        self.assertEqual(
            form.cleaned_data.get("amount_requested"), Decimal("17.0000000000000000017")
        )

    def test_can_set_amounts_to_smaller_than_two_decimal_places_and_see_exactly_two_decimals(
        self,
    ):
        form = UploadContractForm(
            data={"amount_approved": "23", "amount_requested": "31.3"},
            files={"file": self.mock_file},
        )
        self.assertTrue(form.is_valid(), form.errors)

        # Render fields to HTML: triggers widget.render() which calls format_value()
        html_approved = str(form["amount_approved"])
        html_requested = str(form["amount_requested"])

        self.assertIn('value="23.00"', html_approved)
        self.assertIn('value="31.30"', html_requested)

    def test_can_set_amounts_to_larger_than_two_decimal_places_and_see_that_precision(
        self,
    ):
        form = UploadContractForm(
            data={"amount_approved": "23.2323", "amount_requested": "31.313131"},
            files={"file": self.mock_file},
        )
        self.assertTrue(form.is_valid(), form.errors)

        # Render fields to HTML: triggers widget.render() which calls format_value()
        html_approved = str(form["amount_approved"])
        html_requested = str(form["amount_requested"])

        self.assertIn('value="23.2323"', html_approved)
        self.assertIn('value="31.313131"', html_requested)

    def test_can_set_currency_to_USD_with_no_amounts(self):
        form = UploadContractForm(
            data={"currency": "USD"}, files={"file": self.mock_file}
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data.get("currency"), "USD")

    def test_cannot_set_currency_to_two_digits(self):
        form = UploadContractForm(
            data={"currency": "NA"}, files={"file": self.mock_file}
        )
        self.assertFalse(form.is_valid())
        self.assertIn("currency", form.errors.keys())

    def test_zero_amount_with_full_scale_renders_as_zero_not_scientific_notation(self):
        # NUMERIC(38,19) returns Decimal("0.0000000000000000000"), whose
        # str() is "0E-19" -- the widget must not emit "0E-19.00".
        form = UploadContractForm(
            data={
                "amount_approved": "0.0000000000000000000",
                "amount_requested": "0.0000000000000000000",
            },
            files={"file": self.mock_file},
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["amount_approved"], Decimal("0"))
        self.assertEqual(form.cleaned_data["amount_requested"], Decimal("0"))

        html_approved = str(form["amount_approved"])
        html_requested = str(form["amount_requested"])
        self.assertIn('value="0.00"', html_approved)
        self.assertIn('value="0.00"', html_requested)
        self.assertNotIn("E", html_approved)
        self.assertNotIn("E", html_requested)

    def test_blank_amount_renders_empty_not_dot_zero(self):
        # Blank amount on a bound (error) re-render must show empty, NOT ".00".
        # Otherwise a resubmit silently stores 0 -> NUMERIC(38,19) -> 0E-19.
        form = UploadContractForm(
            data={"amount_approved": "", "amount_requested": ""},
            files={"file": self.mock_file},
        )
        # file is required but amount blank is valid -> form may be invalid only
        # due to file; in any case the bound field must not emit ".00".
        html_approved = str(form["amount_approved"])
        html_requested = str(form["amount_requested"])
        self.assertIn('value=""', html_approved)
        self.assertIn('value=""', html_requested)
        self.assertNotIn('value=".00"', html_approved)
        self.assertNotIn('value=".00"', html_requested)


class TestContractFormPaymentsFlowGating(TestCase):
    """The contract forms expose ``amount_requested``, ``amount_approved``
    and ``currency`` only under the DISBURSEMENTS payments flow; under
    INVOICING or DISABLED those fields are popped so the form collects only
    the file and the relevant signed flag.
    """

    amount_fields = ("amount_requested", "amount_approved", "currency")

    def _forms(self):
        # Unbound instances are enough to inspect declared fields after
        # __init__ has run (the gating pops fields there).
        return [
            UploadContractForm(),
            CreateContractForm(),
        ]

    @override_settings(PROJECTS_PAYMENTS_FLOW="DISBURSEMENTS")
    def test_amount_and_currency_fields_present_under_disbursements(self):
        for form in self._forms():
            for field in self.amount_fields:
                self.assertIn(
                    field, form.fields, f"{type(form).__name__} missing {field}"
                )

    @override_settings(PROJECTS_PAYMENTS_FLOW="INVOICING")
    def test_amount_and_currency_fields_hidden_under_invoicing(self):
        for form in self._forms():
            # The file field always remains; only the ledger fields are hidden.
            self.assertIn("file", form.fields)
            for field in self.amount_fields:
                self.assertNotIn(
                    field, form.fields, f"{type(form).__name__} leaked {field}"
                )

    @override_settings(PROJECTS_PAYMENTS_FLOW="DISABLED")
    def test_amount_and_currency_fields_hidden_under_disabled(self):
        for form in self._forms():
            self.assertIn("file", form.fields)
            for field in self.amount_fields:
                self.assertNotIn(
                    field, form.fields, f"{type(form).__name__} leaked {field}"
                )
