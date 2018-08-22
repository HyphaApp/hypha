from django.test import TestCase
from django.urls import reverse

from opentech.apply.users.tests.factories import SuperUserFactory
from opentech.apply.home.factories import ApplyHomePageFactory

from .test_admin_form import form_data


class TestFundCreationView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = SuperUserFactory()
        cls.home = ApplyHomePageFactory()

    def create_page(self, forms=1):
        self.client.force_login(self.user)
        url = reverse('wagtailadmin_pages:add', args=('funds', 'fundtype', self.home.id))

        data = form_data(forms)
        data['action-publish'] = True

        response = self.client.post(url, data=data, secure=True, follow=True)
        self.assertContains(response, 'success')

        self.home.refresh_from_db()
        fund = self.home.get_children().first()

        return fund.specific

    def test_can_create_fund(self):
        fund = self.create_page()
        self.assertEqual(fund.forms.count(), 1)
        self.assertEqual(fund.review_forms.count(), 1)

    def test_can_create_multi_phase_fund(self):
        fund = self.create_page(2)
        self.assertEqual(fund.forms.count(), 2)
        self.assertEqual(fund.review_forms.count(), 2)
