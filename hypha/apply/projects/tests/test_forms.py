import json
from io import BytesIO
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from hypha.apply.home.factories import ApplySiteFactory
from hypha.apply.users.tests.factories import (
    Finance2Factory,
    FinanceFactory,
    StaffFactory,
    UserFactory,
)

from ..files import get_files
from ..forms.payment import (
    ChangeInvoiceStatusForm,
    CreateInvoiceForm,
    EditInvoiceForm,
    SelectDocumentForm,
    filter_request_choices,
)
from ..forms.project import (
    ChangePAFStatusForm,
    FinalApprovalForm,
    ProjectApprovalForm,
    StaffUploadContractForm,
    UploadContractForm,
)
from ..models.payment import (
    APPROVED_BY_FINANCE_1,
    APPROVED_BY_FINANCE_2,
    APPROVED_BY_STAFF,
    CHANGES_REQUESTED_BY_FINANCE_1,
    CHANGES_REQUESTED_BY_FINANCE_2,
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
    address_to_form_data,
)


class TestChangeInvoiceStatusFormForm(TestCase):
    def test_staff_choices_with_submitted_status(self):
        invoice = InvoiceFactory(status=SUBMITTED)
        user = StaffFactory()
        form = ChangeInvoiceStatusForm(instance=invoice, user=user)

        expected = set(filter_request_choices([CHANGES_REQUESTED_BY_STAFF, APPROVED_BY_STAFF, DECLINED], invoice_status_user_choices(user)))
        actual = set(form.fields['status'].choices)
        self.assertEqual(expected, actual)

    def test_finance1_choices_with_submitted_status(self):
        invoice = InvoiceFactory(status=SUBMITTED)
        user = FinanceFactory()
        form = ChangeInvoiceStatusForm(instance=invoice, user=user)

        expected = set(filter_request_choices([CHANGES_REQUESTED_BY_STAFF, APPROVED_BY_STAFF, DECLINED], invoice_status_user_choices(user)))
        actual = set(form.fields['status'].choices)
        self.assertEqual(expected, actual)

    def test_finance2_choices_with_submitted_status(self):
        invoice = InvoiceFactory(status=SUBMITTED)
        user = Finance2Factory()
        form = ChangeInvoiceStatusForm(instance=invoice, user=user)

        expected = set(filter_request_choices([CHANGES_REQUESTED_BY_STAFF, APPROVED_BY_STAFF, DECLINED], invoice_status_user_choices(user)))
        actual = set(form.fields['status'].choices)
        self.assertEqual(expected, actual)

    def test_staff_choices_with_resubmitted_status(self):
        invoice = InvoiceFactory(status=RESUBMITTED)
        user = StaffFactory()
        form = ChangeInvoiceStatusForm(instance=invoice, user=user)

        expected = set(filter_request_choices([CHANGES_REQUESTED_BY_STAFF, APPROVED_BY_STAFF, DECLINED],
                                              invoice_status_user_choices(user)))
        actual = set(form.fields['status'].choices)
        self.assertEqual(expected, actual)

    def test_finance1_choices_with_resubmitted_status(self):
        invoice = InvoiceFactory(status=RESUBMITTED)
        user = FinanceFactory()
        form = ChangeInvoiceStatusForm(instance=invoice, user=user)

        expected = set(filter_request_choices([CHANGES_REQUESTED_BY_STAFF, APPROVED_BY_STAFF, DECLINED],
                                              invoice_status_user_choices(user)))
        actual = set(form.fields['status'].choices)
        self.assertEqual(expected, actual)

    def test_finance2_choices_with_resubmitted_status(self):
        invoice = InvoiceFactory(status=RESUBMITTED)
        user = Finance2Factory()
        form = ChangeInvoiceStatusForm(instance=invoice, user=user)

        expected = set(filter_request_choices([CHANGES_REQUESTED_BY_STAFF, APPROVED_BY_STAFF, DECLINED],
                                              invoice_status_user_choices(user)))
        actual = set(form.fields['status'].choices)
        self.assertEqual(expected, actual)

    def test_staff_choices_with_changes_requested_by_staff_status(self):
        invoice = InvoiceFactory(status=CHANGES_REQUESTED_BY_STAFF)
        user = StaffFactory()
        form = ChangeInvoiceStatusForm(instance=invoice, user=user)

        expected = set(filter_request_choices([DECLINED], invoice_status_user_choices(user)))
        actual = set(form.fields['status'].choices)
        self.assertEqual(expected, actual)

    def test_finance1_choices_with_changes_requested_by_staff_status(self):
        invoice = InvoiceFactory(status=CHANGES_REQUESTED_BY_STAFF)
        user = FinanceFactory()
        form = ChangeInvoiceStatusForm(instance=invoice, user=user)

        expected = set(filter_request_choices([DECLINED], invoice_status_user_choices(user)))
        actual = set(form.fields['status'].choices)
        self.assertEqual(expected, actual)

    def test_finance2_choices_with_changes_requested_by_staff_status(self):
        invoice = InvoiceFactory(status=CHANGES_REQUESTED_BY_STAFF)
        user = Finance2Factory()
        form = ChangeInvoiceStatusForm(instance=invoice, user=user)

        expected = set(filter_request_choices([DECLINED], invoice_status_user_choices(user)))
        actual = set(form.fields['status'].choices)
        self.assertEqual(expected, actual)

    def test_staff_choices_with_approved_by_staff_status(self):
        invoice = InvoiceFactory(status=APPROVED_BY_STAFF)
        user = StaffFactory()
        form = ChangeInvoiceStatusForm(instance=invoice, user=user)

        expected = set(filter_request_choices([CHANGES_REQUESTED_BY_FINANCE_1, APPROVED_BY_FINANCE_1],
                                              invoice_status_user_choices(user)))
        actual = set(form.fields['status'].choices)
        self.assertEqual(expected, actual)

    def test_finance1_choices_with_approved_by_staff_status(self):
        invoice = InvoiceFactory(status=APPROVED_BY_STAFF)
        user = FinanceFactory()
        form = ChangeInvoiceStatusForm(instance=invoice, user=user)

        expected = set(filter_request_choices([CHANGES_REQUESTED_BY_FINANCE_1, APPROVED_BY_FINANCE_1],
                                              invoice_status_user_choices(user)))
        actual = set(form.fields['status'].choices)
        self.assertEqual(expected, actual)

    def test_finance2_choices_with_approved_by_staff_status(self):
        invoice = InvoiceFactory(status=APPROVED_BY_STAFF)
        user = Finance2Factory()
        form = ChangeInvoiceStatusForm(instance=invoice, user=user)

        expected = set(filter_request_choices([CHANGES_REQUESTED_BY_FINANCE_1, APPROVED_BY_FINANCE_1],
                                              invoice_status_user_choices(user)))
        actual = set(form.fields['status'].choices)
        self.assertEqual(expected, actual)

    def test_staff_choices_with_changes_requested_by_finance1_status(self):
        invoice = InvoiceFactory(status=CHANGES_REQUESTED_BY_FINANCE_1)
        user = StaffFactory()
        form = ChangeInvoiceStatusForm(instance=invoice, user=user)

        expected = set(filter_request_choices([CHANGES_REQUESTED_BY_STAFF, DECLINED],
                                              invoice_status_user_choices(user)))
        actual = set(form.fields['status'].choices)
        self.assertEqual(expected, actual)

    def test_finance1_choices_with_changes_requested_by_finance1_status(self):
        invoice = InvoiceFactory(status=CHANGES_REQUESTED_BY_FINANCE_1)
        user = FinanceFactory()
        form = ChangeInvoiceStatusForm(instance=invoice, user=user)

        expected = set(filter_request_choices([CHANGES_REQUESTED_BY_STAFF, DECLINED],
                                              invoice_status_user_choices(user)))
        actual = set(form.fields['status'].choices)
        self.assertEqual(expected, actual)

    def test_finance2_choices_with_changes_requested_by_finance1_status(self):
        invoice = InvoiceFactory(status=CHANGES_REQUESTED_BY_FINANCE_1)
        user = Finance2Factory()
        form = ChangeInvoiceStatusForm(instance=invoice, user=user)

        expected = set(filter_request_choices([CHANGES_REQUESTED_BY_STAFF, DECLINED],
                                              invoice_status_user_choices(user)))
        actual = set(form.fields['status'].choices)
        self.assertEqual(expected, actual)

    def test_staff_choices_with_approved_by_finance1_status(self):
        invoice = InvoiceFactory(status=APPROVED_BY_FINANCE_1)
        user = StaffFactory()
        form = ChangeInvoiceStatusForm(instance=invoice, user=user)

        expected = set(filter_request_choices([CHANGES_REQUESTED_BY_FINANCE_2, APPROVED_BY_FINANCE_2],
                                              invoice_status_user_choices(user)))
        actual = set(form.fields['status'].choices)
        self.assertEqual(expected, actual)

    def test_finance1_choices_with_approved_by_finance1_status(self):
        invoice = InvoiceFactory(status=APPROVED_BY_FINANCE_1)
        user = FinanceFactory()
        form = ChangeInvoiceStatusForm(instance=invoice, user=user)

        expected = set(filter_request_choices([CHANGES_REQUESTED_BY_FINANCE_2, APPROVED_BY_FINANCE_2],
                                              invoice_status_user_choices(user)))
        actual = set(form.fields['status'].choices)
        self.assertEqual(expected, actual)

    def test_finance2_choices_with_approved_by_finance1_status(self):
        invoice = InvoiceFactory(status=APPROVED_BY_FINANCE_1)
        user = Finance2Factory()
        form = ChangeInvoiceStatusForm(instance=invoice, user=user)

        expected = set(filter_request_choices([CHANGES_REQUESTED_BY_FINANCE_2, APPROVED_BY_FINANCE_2],
                                              invoice_status_user_choices(user)))
        actual = set(form.fields['status'].choices)
        self.assertEqual(expected, actual)

    def test_staff_choices_with_changes_requested_by_finance2_status(self):
        invoice = InvoiceFactory(status=CHANGES_REQUESTED_BY_FINANCE_2)
        user = StaffFactory()
        form = ChangeInvoiceStatusForm(instance=invoice, user=user)

        expected = set(filter_request_choices([CHANGES_REQUESTED_BY_FINANCE_1, APPROVED_BY_FINANCE_1],
                                              invoice_status_user_choices(user)))
        actual = set(form.fields['status'].choices)
        self.assertEqual(expected, actual)

    def test_finance1_choices_with_changes_requested_by_finance2_status(self):
        invoice = InvoiceFactory(status=CHANGES_REQUESTED_BY_FINANCE_2)
        user = FinanceFactory()
        form = ChangeInvoiceStatusForm(instance=invoice, user=user)

        expected = set(filter_request_choices([CHANGES_REQUESTED_BY_FINANCE_1, APPROVED_BY_FINANCE_1],
                                              invoice_status_user_choices(user)))
        actual = set(form.fields['status'].choices)
        self.assertEqual(expected, actual)

    def test_finance2_choices_with_changes_requested_by_finance2_status(self):
        invoice = InvoiceFactory(status=CHANGES_REQUESTED_BY_FINANCE_2)
        user = Finance2Factory()
        form = ChangeInvoiceStatusForm(instance=invoice, user=user)

        expected = set(filter_request_choices([CHANGES_REQUESTED_BY_FINANCE_1, APPROVED_BY_FINANCE_1],
                                              invoice_status_user_choices(user)))
        actual = set(form.fields['status'].choices)
        self.assertEqual(expected, actual)

    def test_valid_checks_required_for_approved_by_finance1(self):
        invoice = InvoiceFactory(status=APPROVED_BY_STAFF)
        user = FinanceFactory()
        form = ChangeInvoiceStatusForm(data={'status': APPROVED_BY_FINANCE_1}, instance=invoice, user=user)
        self.assertFalse(form.is_valid(), form.errors.as_text())

        invoice.valid_checks = True
        form = ChangeInvoiceStatusForm(data={'status': APPROVED_BY_FINANCE_1}, instance=invoice, user=user)
        self.assertTrue(form.is_valid(), form.errors.as_text())


class TestChangePAFStatusForm(TestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        apply_site = ApplySiteFactory()
        cls.project_setting, _ = ProjectSettings.objects.get_or_create(site_id=apply_site.id)
        cls.project_setting.use_settings = True
        cls.project_setting.save()
        cls.role = PAFReviewerRoleFactory(page=cls.project_setting)

    def test_paf_status_is_required(self):
        project = ProjectFactory(in_approval=True)
        user = StaffFactory()
        form = ChangePAFStatusForm(data={'role': self.role}, instance=project, user=user)
        self.assertFalse(form.is_valid())
        self.assertIn('paf_status', form.errors.keys())

    def test_role_is_required(self):
        project = ProjectFactory(in_approval=True)
        user = StaffFactory()
        form = ChangePAFStatusForm(data={'paf_status': APPROVE}, instance=project, user=user)
        self.assertFalse(form.is_valid())
        self.assertIn('role', form.errors.keys())

    def test_comment_is_not_required(self):
        project = ProjectFactory(in_approval=True)
        user = StaffFactory()
        form = ChangePAFStatusForm(data={'role': self.role, 'paf_status': APPROVE}, instance=project, user=user)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.errors, {})


class TestFinalApprovalForm(TestCase):
    def test_final_approval_status_is_required(self):
        project = ProjectFactory(in_approval=True)
        user = StaffFactory()
        form = FinalApprovalForm(data={'comment': ''}, instance=project, user=user)
        self.assertFalse(form.is_valid())
        self.assertNotEqual(form.errors, {})
        self.assertIn('final_approval_status', form.errors.keys())

    def test_comment_is_not_required(self):
        project = ProjectFactory(in_approval=True)
        user = StaffFactory()
        form = FinalApprovalForm(data={'final_approval_status': APPROVE}, instance=project, user=user)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.errors, {})


class TestProjectApprovalForm(TestCase):
    def test_updating_fields_sets_changed_flag(self):
        project = ProjectFactory()

        self.assertFalse(project.user_has_updated_details)

        data = {
            'title': f'{project.title} test',
            'value': project.value,
            'proposed_start': project.proposed_start,
            'proposed_end': project.proposed_end,
        }
        data.update(address_to_form_data())
        form = ProjectApprovalForm(instance=project, data=data)
        self.assertTrue(form.is_valid(), form.errors.as_text())

        form.save()

        self.assertTrue(project.user_has_updated_details)


class TestCreateInvoiceForm(TestCase):
    def test_adding_invoice(self):
        data = {
            'paid_value': '10',
            'comment': 'test comment',
        }

        document = SimpleUploadedFile('invoice.pdf', BytesIO(b'somebinarydata').read())
        supporting_documents = [SimpleUploadedFile('invoice.pdf', BytesIO(b'somebinarydata').read())]
        files = {
            'document': document,
            'supporting_documents': supporting_documents
        }

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
            'paid_value': '10',
            'comment': 'test comment',

        }

        document = SimpleUploadedFile('invoice.pdf', BytesIO(b'somebinarydata').read())
        files = {
            'document': document,
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
                'document': invoice.document,
                'supporting_documents-uploads': '[]',
            },
            files={
                'supporting_documents': [],
            },
            instance=invoice)
        self.assertTrue(form.is_valid())

        form.save()
        self.assertFalse(invoice.supporting_documents.exists())

    def test_keep_existing_supporting_document(self):
        invoice = InvoiceFactory()
        supporting_document = SupportingDocumentFactory(invoice=invoice)
        self.assertEqual(invoice.supporting_documents.count(), 1)

        form = EditInvoiceForm(
            data={
                'document': invoice.document,
                'supporting_documents-uploads': json.dumps(
                    [{"name": supporting_document.document.name,
                      "size": supporting_document.document.size,
                      "type": "existing"}]
                ),
            },
            instance=invoice)
        self.assertTrue(form.is_valid())

        invoice = form.save()
        self.assertEqual(invoice.supporting_documents.count(), 1)

    def test_add_new_supporting_document(self):
        invoice = InvoiceFactory()
        self.assertEqual(invoice.supporting_documents.count(), 0)

        supporting_document = [SimpleUploadedFile('invoice.pdf', BytesIO(b'somebinarydata').read())]
        form = EditInvoiceForm(
            data={
                'document': invoice.document,
                'supporting_documents-uploads': '[]',
            },
            files={
                'supporting_documents': supporting_document,
            },
            instance=invoice,
        )
        self.assertTrue(form.is_valid())

        invoice = form.save()
        self.assertEqual(invoice.supporting_documents.count(), 1)


@override_settings(ROOT_URLCONF='hypha.apply.urls')
class TestSelectDocumentForm(TestCase):
    def test_copying_files(self):
        category = DocumentCategoryFactory()
        project = ProjectFactory()

        self.assertEqual(project.packet_files.count(), 0)

        files = list(get_files(project))
        self.assertEqual(len(files), 4)

        url = files[3].url

        form = SelectDocumentForm(
            files,
            data={'category': category.id, 'document': url},
        )
        self.assertTrue(form.is_valid(), form.errors)

        form.instance.project = project
        form.save()

        packet_files = project.packet_files.order_by('id')
        self.assertEqual(len(packet_files), 1)

        self.assertEqual(packet_files.first().document.read(), files[3].read())


class TestStaffContractUploadForm(TestCase):
    mock_file = mock.MagicMock(spec=SimpleUploadedFile)
    mock_file.read.return_value = b"fake file contents"

    def test_staff_can_upload_unsigned(self):
        form = StaffUploadContractForm(data={}, files={'file': self.mock_file})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertFalse(form.cleaned_data.get('is_signed'))

    def test_staff_can_upload_signed(self):
        form = StaffUploadContractForm(data={'is_signed': True}, files={'file': self.mock_file})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertTrue(form.cleaned_data.get('is_signed'))


class TestContractUploadForm(TestCase):
    mock_file = mock.MagicMock(spec=SimpleUploadedFile)
    mock_file.read.return_value = b"fake file contents"

    def test_applicant_cant_upload_unsigned(self):
        form = UploadContractForm(data={}, files={'file': self.mock_file})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertIsNone(form.cleaned_data.get('is_signed'))

    def test_applicant_can_upload_signed(self):
        form = UploadContractForm(data={'is_signed': True}, files={'file': self.mock_file})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertIsNone(form.cleaned_data.get('is_signed'))
