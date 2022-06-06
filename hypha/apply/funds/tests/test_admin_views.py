import factory
from django.contrib.auth.models import Group
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse
from wagtail.tests.utils import WagtailTestUtils

from hypha.apply.funds.models.forms import ApplicationForm
from hypha.apply.home.factories import ApplyHomePageFactory
from hypha.apply.users.groups import STAFF_GROUP_NAME
from hypha.apply.users.tests.factories import SuperUserFactory

from .factories.models import RoundFactory
from .test_admin_form import form_data


def create_form_fields_data(blocks):
    parent_field = 'form_fields'
    form_fields_dict = dict()
    form_fields_dict[f'{parent_field}-count'] = [str(len(blocks))]
    for index, block_name in enumerate(blocks):
        form_fields_dict[f'{parent_field}-{index}-deleted'] = ['']
        form_fields_dict[f'{parent_field}-{index}-order'] = [str(index)]
        form_fields_dict[f'{parent_field}-{index}-type'] = [str(block_name)]

        for field_name, field_value in blocks[block_name].items():
            form_fields_dict[f'{parent_field}-{index}-value-{field_name}'] = field_value

    return form_fields_dict


class TestFundCreationView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = SuperUserFactory()
        cls.home = ApplyHomePageFactory()

    def create_page(self, appl_forms=1, review_forms=1, determination_forms=1, external_review_form=0, stages=1, same_forms=False, form_stage_info=[1]):
        self.client.force_login(self.user)
        url = reverse('wagtailadmin_pages:add', args=('funds', 'fundtype', self.home.id))

        data = form_data(
            appl_forms,
            review_forms,
            determination_forms,
            external_review_form,
            same_forms=same_forms,
            stages=stages,
            form_stage_info=form_stage_info,
        )
        data['action-publish'] = True

        response = self.client.post(url, data=data, secure=True, follow=True)
        try:
            # If the form is present there was an error - report it
            form = response.context['form']
            self.assertTrue(form.is_valid(), form.errors.as_text())
        except KeyError:
            self.assertContains(response, 'success')

        self.home.refresh_from_db()
        fund = self.home.get_children().first()

        return fund.specific

    def test_can_create_fund(self):
        fund = self.create_page()
        self.assertEqual(fund.forms.count(), 1)
        self.assertEqual(fund.review_forms.count(), 1)
        self.assertEqual(fund.determination_forms.count(), 1)

    def test_can_create_fund_with_external_review_form(self):
        fund = self.create_page(1, 1, 1, external_review_form=1, stages=1)
        self.assertEqual(fund.forms.count(), 1)
        self.assertEqual(fund.review_forms.count(), 1)
        self.assertEqual(fund.determination_forms.count(), 1)
        self.assertEqual(fund.external_review_forms.count(), 1)

    def test_can_create_multi_phase_fund(self):
        fund = self.create_page(2, 2, 2, stages=2, form_stage_info=[1, 2])
        self.assertEqual(fund.forms.count(), 2)
        self.assertEqual(fund.review_forms.count(), 2)
        self.assertEqual(fund.determination_forms.count(), 2)

    def test_can_create_multiple_forms_second_stage_in_fund(self):
        fund = self.create_page(4, 2, 2, stages=2, form_stage_info=[1, 2, 2, 2])
        self.assertEqual(fund.forms.count(), 4)
        self.assertEqual(fund.review_forms.count(), 2)
        self.assertEqual(fund.determination_forms.count(), 2)

    def test_can_create_multi_phase_fund_reuse_forms(self):
        fund = self.create_page(2, 2, 2, same_forms=True, stages=2, form_stage_info=[1, 2])
        self.assertEqual(fund.forms.count(), 2)
        self.assertEqual(fund.review_forms.count(), 2)
        self.assertEqual(fund.determination_forms.count(), 2)


class TestRoundIndexView(WagtailTestUtils, TestCase):
    def setUp(self):
        user = self.create_test_user()
        self.client.force_login(user)

        group, _ = Group.objects.get_or_create(name=STAFF_GROUP_NAME)
        group.user_set.add(user)

        self.round = RoundFactory()

    def test_application_links(self):
        response = self.client.get('/admin/funds/round/', follow=True)

        application_links = [
            f'<a href="/admin/funds/applicationform/edit/{app.form.id}/">{app}</a>'
            for app in self.round.forms.all()
        ]
        applications_cell = f'<td class="field-applications title">{"".join(application_links)}</td>'
        self.assertContains(response, applications_cell, html=True)

    def test_number_of_rounds(self):
        response = self.client.get('/admin/funds/round/', follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data["result_count"], 1)

    def test_review_form_links(self):
        response = self.client.get('/admin/funds/round/', follow=True)

        review_form_links = [
            f'<a href="/admin/review/reviewform/edit/{review.form.id}/">{review}</a>'
            for review in self.round.review_forms.all()
        ]
        review_form_cell = f'<td class="field-review_forms title">{"".join(review_form_links)}</td>'
        self.assertContains(response, review_form_cell, html=True)


class TestCreateApplicationFormView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = SuperUserFactory()
        cls.label_help_text_data = {
            'field_label': factory.Faker('sentence').evaluate(None, None, {'locale': None}),
            'help_text': factory.Faker('sentence').evaluate(None, None, {'locale': None})
        }
        cls.name = factory.Faker('name').evaluate(None, None, {'locale': None})

    def create_page(self, data):
        self.client.force_login(self.user)
        url = reverse('funds_applicationform_modeladmin_create')
        response = self.client.post(url, data=data, secure=True, follow=True)
        return response

    def test_name_field_required(self):
        data = {'name': ['']}
        form_field_data = create_form_fields_data(
            {
                'title': self.label_help_text_data,
                'email': self.label_help_text_data,
                'full_name': self.label_help_text_data,
            }
        )
        data.update(form_field_data)
        response = self.create_page(data=data)

        expected_message = 'This field is required.'
        for message in get_messages(response.context['request']):
            self.assertEqual(expected_message, str(message.message).strip())
        self.assertEqual(ApplicationForm.objects.count(), 0)

    def test_title_block_required(self):
        data = {'name': [self.name]}
        form_field_data = create_form_fields_data(
            {
                'email': self.label_help_text_data,
                'full_name': self.label_help_text_data,
            }
        )
        data.update(form_field_data)
        response = self.create_page(data=data)

        expected_message = 'You are missing the following required fields: Title'
        for message in get_messages(response.context['request']):
            self.assertEqual(expected_message, str(message.message).strip())
        self.assertEqual(ApplicationForm.objects.count(), 0)

    def test_email_block_required(self):
        data = {'name': [self.name]}
        form_field_data = create_form_fields_data(
            {
                'title': self.label_help_text_data,
                'full_name': self.label_help_text_data,
            }
        )
        data.update(form_field_data)
        response = self.create_page(data=data)

        expected_message = 'You are missing the following required fields: Email'
        for message in get_messages(response.context['request']):
            self.assertEqual(expected_message, str(message.message).strip())
        self.assertEqual(ApplicationForm.objects.count(), 0)

    def test_full_name_block_required(self):
        data = {'name': [self.name]}
        form_field_data = create_form_fields_data(
            {
                'title': self.label_help_text_data,
                'email': self.label_help_text_data,
            }
        )
        data.update(form_field_data)
        response = self.create_page(data=data)

        expected_message = 'You are missing the following required fields: Full Name'
        for message in get_messages(response.context['request']):
            self.assertEqual(expected_message, str(message.message).strip())
        self.assertEqual(ApplicationForm.objects.count(), 0)

    def test_field_label_required(self):
        data = {'name': [self.name]}
        form_field_data = create_form_fields_data(
            {
                'title': {},
                'email': {},
                'full_name': {},
            }
        )
        data.update(form_field_data)
        response = self.create_page(data=data)

        expected_messages_list = ['Label cannot be empty for Application title', 'Label cannot be empty for Email', 'Label cannot be empty for Full name']
        for message in get_messages(response.context['request']):
            self.assertIn(str(message.message).strip(), expected_messages_list)
        self.assertEqual(ApplicationForm.objects.count(), 0)

    def test_form_creation(self):
        data = {'name': [self.name]}
        form_field_data = create_form_fields_data(
            {
                'title': self.label_help_text_data,
                'email': self.label_help_text_data,
                'full_name': self.label_help_text_data,
            }
        )
        data.update(form_field_data)
        response = self.create_page(data=data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ApplicationForm.objects.count(), 1)
