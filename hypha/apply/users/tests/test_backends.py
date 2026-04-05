"""Tests for the custom authentication backend."""

from django.test import RequestFactory, TestCase

from ..backends import CustomModelBackend
from .factories import UserFactory


class TestCustomModelBackend(TestCase):
    def setUp(self):
        self.backend = CustomModelBackend()
        self.factory = RequestFactory()
        self.request = self.factory.get("/")
        self.password = "securepass123"
        self.user = UserFactory(email="user@example.com")
        self.user.set_password(self.password)
        self.user.save()

    def test_authenticate_with_valid_credentials(self):
        result = self.backend.authenticate(
            self.request, username="user@example.com", password=self.password
        )
        self.assertEqual(result, self.user)

    def test_authenticate_case_insensitive_email(self):
        result = self.backend.authenticate(
            self.request, username="USER@EXAMPLE.COM", password=self.password
        )
        self.assertEqual(result, self.user)

    def test_authenticate_wrong_password(self):
        result = self.backend.authenticate(
            self.request, username="user@example.com", password="wrongpassword"
        )
        self.assertIsNone(result)

    def test_authenticate_nonexistent_user(self):
        # Should return None and not raise an exception (timing attack protection)
        result = self.backend.authenticate(
            self.request, username="ghost@example.com", password="anypassword"
        )
        self.assertIsNone(result)

    def test_authenticate_none_username_returns_none(self):
        result = self.backend.authenticate(self.request, username=None, password="pass")
        self.assertIsNone(result)

    def test_authenticate_none_password_returns_none(self):
        result = self.backend.authenticate(
            self.request, username="user@example.com", password=None
        )
        self.assertIsNone(result)

    def test_authenticate_both_none_returns_none(self):
        result = self.backend.authenticate(self.request, username=None, password=None)
        self.assertIsNone(result)

    def test_authenticate_inactive_user_returns_none(self):
        self.user.is_active = False
        self.user.save()
        result = self.backend.authenticate(
            self.request, username="user@example.com", password=self.password
        )
        self.assertIsNone(result)
