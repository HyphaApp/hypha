from django.core import mail
from django.test import TestCase

from hypha.apply.users.tests.factories import UserFactory

from ..utils import get_user_by_email, is_user_already_registered, send_activation_email


class TestActivationEmail(TestCase):
    def test_activation_email_includes_link(self):
        send_activation_email(UserFactory())
        assert len(mail.outbox) == 1
        email_body = mail.outbox[0].body
        assert "password reset form at: https://primary-test-host.org" in email_body


class TestGetUserByEmail(TestCase):
    def test_no_account(self):
        assert get_user_by_email(email="abc@gmail.com") is None

    def test_single_same_email(self):
        user1 = UserFactory(email="abc@gmail.com")

        assert get_user_by_email(email="abc@gmail.com").id == user1.id
        assert get_user_by_email(email="ABC@gmail.com").id == user1.id
        assert get_user_by_email(email="ABC@GMAIL.COM").id == user1.id

    def test_multiple_accounts_same_email(self):
        user1 = UserFactory(email="abc@gmail.com")
        user2 = UserFactory(email="Abc@gmail.com")

        assert get_user_by_email(email="abc@gmail.com").id == user1.id
        assert get_user_by_email(email="Abc@gmail.com").id == user2.id


class TestUserAlreadyRegistered(TestCase):
    def test_no_account(self):
        assert is_user_already_registered(email="abc@gmail.com") == (False, "")

    def test_case_sensitive_email(self):
        UserFactory(email="abc@gmail.com")

        assert is_user_already_registered(email="abc@gmail.com") == (
            True,
            "Email is already in use.",
        )
        assert is_user_already_registered(email="ABc@gmail.com") == (
            True,
            "Email is already in use.",
        )
