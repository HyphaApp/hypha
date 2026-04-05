"""Tests for PasswordlessAuthService."""

from django.core import mail
from django.test import RequestFactory, TestCase, override_settings

from ..models import PendingSignup
from ..services import PasswordlessAuthService
from .factories import UserFactory


class TestPasswordlessAuthServiceUrlParams(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _make_service(self, path="/", next_url=None, extended_session=False):
        if next_url:
            request = self.factory.get(path, {"next": next_url})
        else:
            request = self.factory.get(path)
        return PasswordlessAuthService(request, extended_session=extended_session)

    def test_no_params_returns_none(self):
        service = self._make_service()
        assert service._get_url_params() is None

    def test_with_next_url_includes_next(self):
        service = self._make_service(next_url="/dashboard/")
        params = service._get_url_params()
        assert params is not None
        assert "next=/dashboard/" in params

    def test_with_extended_session_includes_remember_me(self):
        service = self._make_service(extended_session=True)
        params = service._get_url_params()
        assert params is not None
        assert "remember-me" in params

    def test_with_both_includes_both(self):
        service = self._make_service(next_url="/dashboard/", extended_session=True)
        params = service._get_url_params()
        assert "next=/dashboard/" in params
        assert "remember-me" in params


class TestPasswordlessAuthServiceInitiateLoginSignup(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.post("/account/login/")

    def _make_service(self):
        return PasswordlessAuthService(self.request)

    def test_existing_user_receives_login_email(self):
        user = UserFactory(email="existing@example.com")
        service = self._make_service()
        service.initiate_login_signup(email=user.email)

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(user.email, mail.outbox[0].to)
        self.assertIn("Log in to", mail.outbox[0].subject)

    @override_settings(ENABLE_PUBLIC_SIGNUP=False)
    def test_nonexistent_user_signup_disabled_receives_no_email(self):
        service = self._make_service()
        service.initiate_login_signup(email="ghost@example.com")

        self.assertEqual(len(mail.outbox), 0)

    @override_settings(ENABLE_PUBLIC_SIGNUP=True)
    def test_nonexistent_user_signup_enabled_creates_pending_signup(self):
        service = self._make_service()
        service.initiate_login_signup(email="newuser@example.com")

        self.assertTrue(
            PendingSignup.objects.filter(email="newuser@example.com").exists()
        )

    @override_settings(ENABLE_PUBLIC_SIGNUP=True)
    def test_nonexistent_user_signup_enabled_sends_new_account_email(self):
        service = self._make_service()
        service.initiate_login_signup(email="newuser@example.com")

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("newuser@example.com", mail.outbox[0].to)
        self.assertIn("Welcome", mail.outbox[0].subject)

    def test_login_email_contains_magic_link_path(self):
        user = UserFactory(email="magic@example.com")
        service = self._make_service()
        service.initiate_login_signup(email=user.email)

        self.assertIn("/account/auth/", mail.outbox[0].body)
