from django.test import TestCase
from django.urls import reverse

from .factories import OAuthUserFactory, StaffFactory, UserFactory


class BaseTestProfielView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('users:account')


class TestProfileView(BaseTestProfielView):
    def setUp(self):
        self.user = UserFactory()
        self.client.force_login(self.user)

    def test_cant_acces_if_not_logged_in(self):
        self.client.logout()
        response = self.client.get(self.url, follow=True)
        # Initial redirect will be via to https through a 301
        self.assertRedirects(response, reverse('users:login') + '?next=' + self.url, status_code=301)

    def test_includes_change_password(self):
        response = self.client.get(self.url, follow=True)
        self.assertContains(response, reverse('users:password_change'))

    def test_doesnt_includes_change_password_for_oauth(self):
        self.client.force_login(OAuthUserFactory())
        response = self.client.get(self.url, follow=True)
        self.assertNotContains(response, reverse('users:password_change'))

    def test_cant_set_slack_name(self):
        response = self.client.get(self.url, follow=True)
        self.assertNotContains(response, 'Slack name')


class TestStaffProfileView(BaseTestProfielView):
    def setUp(self):
        self.staff = StaffFactory()
        self.client.force_login(self.staff)

    def test_can_set_slack_name(self):
        response = self.client.get(self.url, follow=True)
        self.assertContains(response, 'Slack name')
