from django.test import TestCase
from django.urls import reverse

from .factories import UserFactory

LOGIN_URL = reverse("users:login")
PASSWORD_RESET_URL = reverse("users:password_reset")

# Default rate limit is 5/m — one more request than the limit triggers a 403.
RATE_LIMIT = 5


class TestLoginViewRateLimit(TestCase):
    """Login view is protected by an IP-based rate limit on POST requests."""

    def _post_login(self, email="test@example.com"):
        return self.client.post(
            LOGIN_URL,
            data={
                "login_view-current_step": "auth",
                "auth-username": email,
                "auth-password": "wrong-password",
            },
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
