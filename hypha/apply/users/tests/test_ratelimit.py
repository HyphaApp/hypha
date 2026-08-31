from django.test import TestCase
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from ..tokens import PasswordlessLoginTokenGenerator
from .factories import UserFactory

LOGIN_URL = reverse("users:login")
PASSWORD_RESET_URL = reverse("users:password_reset")

# Default rate limit is 5/m — one more request than the limit triggers a 403.
RATE_LIMIT = 5


class TestLoginViewRateLimit(TestCase):
    """Login view is rate-limited by both IP and account.

    The account key has to read `auth-username`: the view is a two-factor
    wizard, so it prefixes its form fields and there is no plain `email` field
    to key on.
    """

    def _post_login(self, email="test@example.com", ip="127.0.0.1"):
        return self.client.post(
            LOGIN_URL,
            data={
                "login_view-current_step": "auth",
                "auth-username": email,
                "auth-password": "wrong-password",
            },
            REMOTE_ADDR=ip,
        )

    def test_login_accessible_before_limit(self):
        response = self._post_login()
        # Bad credentials returns the form again (200), not 403.
        self.assertNotEqual(response.status_code, 403)

    def test_login_blocked_after_ip_limit_exceeded(self):
        for _ in range(RATE_LIMIT):
            self._post_login()
        response = self._post_login()
        self.assertEqual(response.status_code, 403)

    def test_login_blocked_after_account_limit_exceeded(self):
        """Password-spraying one account is throttled across IPs."""
        user = UserFactory()
        for i in range(RATE_LIMIT):
            self._post_login(email=user.email, ip=f"10.0.0.{i}")
        response = self._post_login(email=user.email, ip="10.0.0.99")
        self.assertEqual(response.status_code, 403)

    def test_account_limit_does_not_lock_out_other_accounts(self):
        """A per-account key must not collapse into one site-wide bucket.

        If it does, anyone can exhaust the limit and block password login for
        every user — an unauthenticated denial of service.
        """
        victim = UserFactory()
        for i in range(RATE_LIMIT):
            self._post_login(email=f"attacker{i}@example.com", ip=f"10.0.0.{i}")
        response = self._post_login(email=victim.email, ip="10.0.0.99")
        self.assertNotEqual(response.status_code, 403)

    def test_username_key_is_case_and_whitespace_insensitive(self):
        """Casing the address differently must not buy a fresh bucket."""
        user = UserFactory(email="Victim@Example.com")
        for i in range(RATE_LIMIT):
            self._post_login(email=f" {user.email.upper()} ", ip=f"10.0.0.{i}")
        response = self._post_login(email=user.email.lower(), ip="10.0.0.99")
        self.assertEqual(response.status_code, 403)


class TestPasswordlessLoginRateLimit(TestCase):
    """`PasswordlessLoginView` inherits `LoginView`'s decorated `dispatch`.

    Its POSTs carry no username, so they key on IP — one user clicking a magic
    link must never consume a budget shared with everyone else's.
    """

    def _confirm_login(self, user, ip):
        url = reverse(
            "users:do_passwordless_login",
            kwargs={
                "uidb64": urlsafe_base64_encode(force_bytes(user.pk)),
                "token": PasswordlessLoginTokenGenerator().make_token(user),
            },
        )
        return self.client.post(url, REMOTE_ADDR=ip)

    def test_one_users_confirmations_do_not_block_another(self):
        for i in range(RATE_LIMIT):
            self._confirm_login(UserFactory(), ip=f"10.0.1.{i}")
        response = self._confirm_login(UserFactory(), ip="10.0.1.99")
        self.assertNotEqual(response.status_code, 403)


class TestPasswordResetRateLimit(TestCase):
    """Password reset view is rate-limited by both IP and email address."""

    def _post_reset(self, email="victim@example.com"):
        return self.client.post(PASSWORD_RESET_URL, data={"email": email})

    def test_password_reset_accessible_before_limit(self):
        response = self._post_reset()
        # First request should not be blocked (redirect or 200).
        self.assertNotEqual(response.status_code, 403)

    def test_password_reset_blocked_after_ip_limit_exceeded(self):
        for _ in range(RATE_LIMIT):
            self._post_reset()
        response = self._post_reset()
        self.assertEqual(response.status_code, 403)

    def test_password_reset_blocked_after_email_limit_exceeded(self):
        # The email-based key limits enumeration of specific accounts.
        user = UserFactory()
        for _ in range(RATE_LIMIT):
            self._post_reset(email=user.email)
        response = self._post_reset(email=user.email)
        self.assertEqual(response.status_code, 403)
