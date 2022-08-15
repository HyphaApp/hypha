from django.core import mail
from django.test import TestCase, override_settings

from hypha.apply.users.tests.factories import UserFactory

from ..utils import send_activation_email


@override_settings(ROOT_URLCONF='hypha.apply.urls')
class TestActivationEmail(TestCase):

    def test_activation_email_includes_link(self):
        send_activation_email(UserFactory())
        assert len(mail.outbox) == 1
        email_body = mail.outbox[0].body
        assert "password reset form at: https://primary-test-host.org" in email_body
