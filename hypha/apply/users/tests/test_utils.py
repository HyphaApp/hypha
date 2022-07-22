from django.core import mail
from django.test import TestCase, override_settings
from django.conf import settings

from hypha.apply.users.tests.factories import UserFactory

from ..utils import send_activation_email


@override_settings(ROOT_URLCONF='hypha.apply.urls')
class TestActivationEmail(TestCase):
    def test_activation_email_includes_link(self):
        send_activation_email(UserFactory())
        self.assertEqual(len(mail.outbox), 1)
        self.assertContains(mail.outbox[0], settings.WAGTAILADMIN_BASE_URL)
