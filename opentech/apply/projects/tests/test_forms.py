from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from opentech.apply.users.tests.factories import UserFactory

from ..files import get_files
from ..forms import (
    ChangePaymentRequestStatusForm,
    ProjectApprovalForm,
    RequestPaymentForm,
    SelectDocumentForm,
    filter_choices,
    filter_request_choices
)
from ..models import CHANGES_REQUESTED, DECLINED, PAID, SUBMITTED, UNDER_REVIEW
from .factories import (
    DocumentCategoryFactory,
    PaymentRequestFactory,
    ProjectFactory,
    address_to_form_data
)


class TestChangePaymentRequestStatusForm(TestCase):
    def test_choices_with_submitted_status(self):
        request = PaymentRequestFactory(status=SUBMITTED)
        form = ChangePaymentRequestStatusForm(instance=request)

        expected = set(filter_request_choices([UNDER_REVIEW, CHANGES_REQUESTED, DECLINED, PAID]))
        actual = set(form.fields['status'].choices)

        self.assertEqual(expected, actual)

    def test_choices_with_changes_requested_status(self):
        request = PaymentRequestFactory(status=CHANGES_REQUESTED)
        form = ChangePaymentRequestStatusForm(instance=request)

        expected = set(filter_request_choices([DECLINED]))
        actual = set(form.fields['status'].choices)

        self.assertEqual(expected, actual)

    def test_choices_with_under_review_status(self):
        request = PaymentRequestFactory(status=UNDER_REVIEW)
        form = ChangePaymentRequestStatusForm(instance=request)

        expected = set(filter_request_choices([PAID]))
        actual = set(form.fields['status'].choices)

        self.assertEqual(expected, actual)

    def test_filter_choices(self):
        ONE = 'one'
        TWO = 'two'
        choices = [
            (ONE, 'One'),
            (TWO, 'Two'),
        ]

        output = filter_choices(choices, [ONE, TWO])
        self.assertTrue(output, choices)

        # order shouldn't matter
        output = filter_choices(choices, [TWO, ONE])
        self.assertTrue(output, choices)

        # duplicates shouldn't matter
        output = filter_choices(choices, [TWO, ONE, TWO])
        self.assertTrue(output, choices)

        output = filter_choices(choices, [TWO])
        self.assertTrue(output, [(TWO, 'Two')])


class TestProjectApprovalForm(TestCase):
    def test_updating_fields_sets_changed_flag(self):
        project = ProjectFactory()

        self.assertFalse(project.user_has_updated_details)

        data = {
            'title': f'{project.title} test',
            'contact_legal_name': project.contact_legal_name,
            'contact_email': project.contact_email,
            'contact_phone': project.contact_phone,
            'value': project.value,
            'proposed_start': project.proposed_start,
            'proposed_end': project.proposed_end,
        }
        data.update(address_to_form_data())
        form = ProjectApprovalForm(instance=project, data=data)
        form.save()

        self.assertTrue(project.user_has_updated_details)


class TestRequestPaymentForm(TestCase):
    def test_adding_payment_request(self):
        data = {
            'value': '10',
            'date_from': '2018-08-15',
            'date_to': '2019-08-15',
            'comment': 'test comment',
        }

        invoice = SimpleUploadedFile('invoice.pdf', BytesIO(b'somebinarydata').read())
        receipts = SimpleUploadedFile('receipts.pdf', BytesIO(b'someotherbinarydata').read())
        files = {
            'invoice': invoice,
            'receipts': receipts,
        }

        form = RequestPaymentForm(data=data, files=files)
        self.assertTrue(form.is_valid(), msg=form.errors)

        form.instance.by = UserFactory()
        form.instance.project = ProjectFactory()
        payment_request = form.save()

        self.assertEqual(payment_request.receipts.count(), 1)

    def test_payment_request_dates_are_correct(self):
        invoice = SimpleUploadedFile('invoice.pdf', BytesIO(b'somebinarydata').read())
        receipts = SimpleUploadedFile('receipts.pdf', BytesIO(b'someotherbinarydata').read())
        files = {
            'invoice': invoice,
            'receipts': receipts,
        }

        form = RequestPaymentForm(
            files=files,
            data={
                'value': '10',
                'date_from': '2018-08-15',
                'date_to': '2019-08-15',
                'comment': 'test comment',
            }
        )
        self.assertTrue(form.is_valid(), msg=form.errors)

        form = RequestPaymentForm(
            files=files,
            data={
                'value': '10',
                'date_from': '2019-08-15',
                'date_to': '2018-08-15',
                'comment': 'test comment',
            }
        )
        self.assertFalse(form.is_valid())


@override_settings(ROOT_URLCONF='opentech.apply.urls')
class TestSelectDocumentForm(TestCase):
    def test_copying_files(self):
        category = DocumentCategoryFactory()
        project = ProjectFactory()

        self.assertEqual(project.packet_files.count(), 0)

        files = list(get_files(project))
        self.assertEqual(len(files), 4)

        urls = [files[0].url, files[2].url]

        form = SelectDocumentForm(
            files,
            project,
            data={'category': category.id, 'files': urls},
        )
        self.assertTrue(form.is_valid(), form.errors)

        form.save()

        packet_files = project.packet_files.order_by('id')
        self.assertEqual(len(packet_files), 2)

        first_file, second_file = packet_files
        self.assertEqual(first_file.document.read(), files[0].read())
        self.assertEqual(second_file.document.read(), files[2].read())
