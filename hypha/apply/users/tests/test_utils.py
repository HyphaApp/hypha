from test.support import EnvironmentVarGuard

from django.core import mail
from django.test import TestCase, override_settings

from hypha.apply.users.tests.factories import UserFactory

from ..utils import send_activation_email


@override_settings(ROOT_URLCONF='hypha.apply.urls')
class TestActivationEmail(TestCase):
    def setUp(self) -> None:
        self.env = EnvironmentVarGuard()
        self.env.set('PRIMARY_HOST', 'primary-domain.org')

    def test_activation_email_includes_link(self):
        with self.env:
            send_activation_email(UserFactory())
            assert len(mail.outbox) == 1
            assert "password reset form at https://primary-domain.org" in mail.outbox[0]
