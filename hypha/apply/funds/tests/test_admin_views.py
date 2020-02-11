from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from wagtail.tests.utils import WagtailTestUtils

from opentech.apply.home.factories import ApplyHomePageFactory
from opentech.apply.users.groups import STAFF_GROUP_NAME
from opentech.apply.users.tests.factories import SuperUserFactory

from .factories.models import RoundFactory
from .test_admin_form import form_data


class TestFundCreationView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = SuperUserFactory()
        cls.home = ApplyHomePageFactory()

    def create_page(self, appl_forms=1, review_forms=1, stages=1, same_forms=False, form_stage_info=[1]):
        self.client.force_login(self.user)
        url = reverse('wagtailadmin_pages:add', args=('funds', 'fundtype', self.home.id))

        data = form_data(
            appl_forms,
            review_forms,
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

    def test_can_create_multi_phase_fund(self):
        fund = self.create_page(2, 2, stages=2, form_stage_info=[1, 2])
        self.assertEqual(fund.forms.count(), 2)
        self.assertEqual(fund.review_forms.count(), 2)

    def test_can_create_multiple_forms_second_stage_in_fund(self):
        fund = self.create_page(4, 2, stages=2, form_stage_info=[1, 2, 2, 2])
        self.assertEqual(fund.forms.count(), 4)
        self.assertEqual(fund.review_forms.count(), 2)

    def test_can_create_multi_phase_fund_reuse_forms(self):
        fund = self.create_page(2, 2, same_forms=True, stages=2, form_stage_info=[1, 2])
        self.assertEqual(fund.forms.count(), 2)
        self.assertEqual(fund.review_forms.count(), 2)


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
        applications_cell = f'<td class="field-applications">{"".join(application_links)}</td>'
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
        review_form_cell = f'<td class="field-review_forms">{"".join(review_form_links)}</td>'
        self.assertContains(response, review_form_cell, html=True)
