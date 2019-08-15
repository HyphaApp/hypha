from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from opentech.apply.users.tests.factories import UserFactory

from ..forms import ProjectApprovalForm, RequestPaymentForm
from .factories import ProjectFactory, address_to_form_data


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
