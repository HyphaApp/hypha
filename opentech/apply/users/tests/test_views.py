from django.test import TestCase
from django.urls import reverse

from .factories import OAuthUserFactory, UserFactory


class TestProfileView(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.url = reverse('users:account')

    def test_cant_acces_if_not_logged_in(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('users:login') + '?next=' + self.url)

    def test_includes_change_password(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertContains(response, reverse('users:password_change'))

    def test_doesnt_includes_change_password_for_oauth(self):
        self.client.force_login(OAuthUserFactory())
        response = self.client.get(self.url)
        self.assertNotContains(response, reverse('users:password_change'))

    def test_email_unique(self):
        other_user = UserFactory()
        self.client.post(self.url, data={'email': other_user.email})
        self.user.refresh_from_db()
        self.assertNotEqual(self.user.email, other_user.email)

    def test_can_change_email(self):
        new_email = 'me@another.com'
        self.client.force_login(self.user)
        self.client.post(self.url, data={'email': new_email})
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, new_email)
