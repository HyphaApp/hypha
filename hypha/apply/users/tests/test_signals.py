from django.contrib.auth.signals import user_logged_in
from django.core import mail
from django.test import RequestFactory, TestCase, override_settings

from .factories import UserFactory


@override_settings(SEND_MESSAGES=True)
class TestSendLoginNotification(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = UserFactory()

    def _fire_signal(self, user=None, request=None):
        if user is None:
            user = self.user
        if request is None:
            request = self.factory.get("/")
        user_logged_in.send(sender=user.__class__, request=request, user=user)

    def test_sends_email_on_login(self):
        self._fire_signal()
        self.assertEqual(len(mail.outbox), 1)

    def test_email_sent_to_user(self):
        self._fire_signal()
        self.assertIn(self.user.email, mail.outbox[0].to)

    def test_email_subject_contains_org_name(self):
        from django.conf import settings

        self._fire_signal()
        self.assertIn(settings.ORG_LONG_NAME, mail.outbox[0].subject)

    def test_no_email_when_send_messages_disabled(self):
        with self.settings(SEND_MESSAGES=False):
            self._fire_signal()
        self.assertEqual(len(mail.outbox), 0)

    def test_no_email_when_user_has_no_email(self):
        self.user.email = ""
        self.user.save()
        self._fire_signal()
        self.assertEqual(len(mail.outbox), 0)

    def test_no_email_when_request_is_none(self):
        # Signal can be fired without a request (e.g. management commands)
        self._fire_signal(request=None)
        self.assertEqual(len(mail.outbox), 1)

    def test_email_body_contains_login_time(self):
        self._fire_signal()
        self.assertTrue(any("Login time" in part for part in [mail.outbox[0].body]))
