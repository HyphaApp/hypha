import factory
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from hypha.apply.determinations.models import DeterminationForm
from hypha.apply.funds.tests.test_admin_views import create_form_fields_data
from hypha.apply.users.tests.factories import SuperUserFactory


class TestCreateDeterminationFormView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = SuperUserFactory()
        cls.label_help_text_data = {
            'field_label': factory.Faker('sentence').evaluate(None, None, {'locale': None}),
            'field_help_text': factory.Faker('sentence').evaluate(None, None, {'locale': None})
        }
        cls.send_notice_data = {
            'field_label': factory.Faker('sentence').evaluate(None, None, {'locale': None}),
            'field_help_text': factory.Faker('sentence').evaluate(None, None, {'locale': None}),
            'default_value': True,
        }
        cls.name = factory.Faker('name').evaluate(None, None, {'locale': None})

    def create_page(self, data):
        self.client.force_login(self.user)
        url = reverse('determinations_determinationform_modeladmin_create')
        response = self.client.post(url, data=data, secure=True, follow=True)
        return response

    def test_name_field_required(self):
        data = {'name': ['']}
        form_field_data = create_form_fields_data(
            {
                'determination': self.label_help_text_data,
                'message': self.label_help_text_data,
                'send_notice': self.send_notice_data,
            }
        )
        data.update(form_field_data)
        response = self.create_page(data=data)

        expected_message = 'This field is required.'
        for message in get_messages(response.context['request']):
            self.assertEqual(expected_message, str(message.message).strip())
        self.assertEqual(DeterminationForm.objects.count(), 0)

    def test_determination_block_required(self):
        data = {'name': [self.name]}
        form_field_data = create_form_fields_data(
            {
                'message': self.label_help_text_data,
                'send_notice': self.send_notice_data,
            }
        )
        data.update(form_field_data)
        response = self.create_page(data=data)

        expected_message = 'You are missing the following required fields: Determination'
        for message in get_messages(response.context['request']):
            self.assertEqual(expected_message, str(message.message).strip())
        self.assertEqual(DeterminationForm.objects.count(), 0)

    def test_message_block_required(self):
        data = {'name': [self.name]}
        form_field_data = create_form_fields_data(
            {
                'determination': self.label_help_text_data,
                'send_notice': self.send_notice_data,
            }
        )
        data.update(form_field_data)
        response = self.create_page(data=data)

        expected_message = 'You are missing the following required fields: Message'
        for message in get_messages(response.context['request']):
            self.assertEqual(expected_message, str(message.message).strip())
        self.assertEqual(DeterminationForm.objects.count(), 0)

    def test_send_notice_block_required(self):
        data = {'name': [self.name]}
        form_field_data = create_form_fields_data(
            {
                'determination': self.label_help_text_data,
                'message': self.label_help_text_data,
            }
        )
        data.update(form_field_data)
        response = self.create_page(data=data)

        expected_message = 'You are missing the following required fields: Send Notice'
        for message in get_messages(response.context['request']):
            self.assertEqual(expected_message, str(message.message).strip())
        self.assertEqual(DeterminationForm.objects.count(), 0)

    def test_field_label_required(self):
        data = {'name': [self.name]}
        form_field_data = create_form_fields_data(
            {
                'determination': {},
                'message': {},
                'send_notice': self.send_notice_data,
            }
        )
        data.update(form_field_data)
        response = self.create_page(data=data)

        expected_messages_list = ['Label cannot be empty for Determination', 'Label cannot be empty for Message']
        for message in get_messages(response.context['request']):
            self.assertIn(str(message.message).strip(), expected_messages_list)
        self.assertEqual(DeterminationForm.objects.count(), 0)

    def test_form_creation(self):
        data = {'name': [self.name]}
        form_field_data = create_form_fields_data(
            {
                'determination': self.label_help_text_data,
                'message': self.label_help_text_data,
                'send_notice': self.send_notice_data,
            }
        )
        data.update(form_field_data)
        response = self.create_page(data=data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(DeterminationForm.objects.count(), 1)
