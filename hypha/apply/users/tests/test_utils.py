from django.core import mail
from django.test import TestCase, override_settings

from hypha.apply.users.tests.factories import UserFactory

from ..utils import get_user_by_email, send_activation_email


@override_settings(ROOT_URLCONF='hypha.apply.urls')
class TestActivationEmail(TestCase):

    def test_activation_email_includes_link(self):
        send_activation_email(UserFactory())
        assert len(mail.outbox) == 1
        email_body = mail.outbox[0].body
        assert "password reset form at: https://primary-test-host.org" in email_body


@override_settings(ROOT_URLCONF='hypha.apply.urls')
class TestUserByEmail(TestCase):

    def setUp(self):
        self.user1 = UserFactory(email='abc@gmail.com')
        self.user2 = UserFactory(email='Abc@gmail.com')

    def test_get_user_by_email_with_sensitive_search(self):
        exact_user = get_user_by_email(email='abc@gmail.com')
        self.assertEqual(exact_user.email, self.user1.email)
        self.assertNotEqual(exact_user.email, self.user2.email)
        exact_user = get_user_by_email(email='ABC@gmail.com')
        self.assertIsNone(exact_user)

    def test_get_user_by_email_without_sensitive_search(self):
        exact_user = get_user_by_email(email='ABC@gmail.com', sensitive_search=0)
        self.assertIsNotNone(exact_user)
        self.assertIn(exact_user.email, [self.user1.email, self.user2.email])
