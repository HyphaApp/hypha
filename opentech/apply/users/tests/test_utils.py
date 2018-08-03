from django.core import mail
from django.test import TestCase

from opentech.apply.users.tests.factories import UserFactory

from ..utils import send_activation_email


class TestActivationEmail(TestCase):
    def test_activation_email_includes_link(self):
        send_activation_email(UserFactory())
        self.assertEqual(len(mail.outbox), 1)
