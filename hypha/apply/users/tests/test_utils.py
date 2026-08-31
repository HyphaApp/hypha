from django.core import mail
from django.test import RequestFactory, TestCase, override_settings

from ..utils import (
    get_redirect_url,
    get_user_by_email,
    is_user_already_registered,
    send_activation_email,
    send_confirmation_email,
    strip_html_and_nerf_urls,
    update_is_staff,
)
from .factories import StaffFactory, UserFactory


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


class TestSendConfirmationEmail(TestCase):
    def test_sends_email_to_updated_address(self):
        user = UserFactory(email="old@example.com")
        send_confirmation_email(
            user,
            token="fake-token",
            updated_email="new@example.com",
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("new@example.com", mail.outbox[0].to)

    def test_email_subject_contains_new_address(self):
        user = UserFactory(email="old@example.com")
        send_confirmation_email(
            user,
            token="fake-token",
            updated_email="new@example.com",
        )
        self.assertIn("new@example.com", mail.outbox[0].subject)

    def test_sends_to_user_when_no_updated_email(self):
        user = UserFactory(email="user@example.com")
        send_confirmation_email(user, token="fake-token")
        self.assertEqual(len(mail.outbox), 1)


class TestGetRedirectUrl(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_safe_relative_url_from_get(self):
        request = self.factory.get("/login/", {"next": "/dashboard/"})
        result = get_redirect_url(request, "next")
        self.assertEqual(result, "/dashboard/")

    def test_safe_relative_url_from_post(self):
        request = self.factory.post("/login/", {"next": "/dashboard/"})
        result = get_redirect_url(request, "next")
        self.assertEqual(result, "/dashboard/")

    @override_settings(ALLOWED_HOSTS=["example.com"])
    def test_external_url_returns_empty_string(self):
        request = self.factory.get("/login/", {"next": "https://evil.com/steal"})
        request.META["HTTP_HOST"] = "example.com"
        result = get_redirect_url(request, "next")
        self.assertEqual(result, "")

    def test_missing_next_param_returns_empty_string(self):
        request = self.factory.get("/login/")
        result = get_redirect_url(request, "next")
        self.assertEqual(result, "")

    def test_post_takes_precedence_over_get(self):
        request = self.factory.post("/login/?next=/from-get/", {"next": "/from-post/"})
        result = get_redirect_url(request, "next")
        self.assertEqual(result, "/from-post/")


class TestUpdateIsStaff(TestCase):
    def test_sets_is_staff_when_staff_admin(self):
        user = StaffFactory()
        # Make user a staff admin (has TEAMADMIN group)
        from django.contrib.auth.models import Group

        from hypha.apply.users.roles import TEAMADMIN_GROUP_NAME

        admin_group, _ = Group.objects.get_or_create(name=TEAMADMIN_GROUP_NAME)
        user.groups.add(admin_group)
        # Clear cached properties
        if "is_apply_staff_admin" in user.__dict__:
            del user.__dict__["is_apply_staff_admin"]

        user.is_staff = False
        user.save()

        update_is_staff(None, user)
        user.refresh_from_db()
        self.assertTrue(user.is_staff)

    def test_clears_is_staff_when_not_staff_admin(self):
        user = UserFactory()
        user.is_staff = True
        user.save()

        update_is_staff(None, user)
        user.refresh_from_db()
        self.assertFalse(user.is_staff)

    def test_no_change_when_already_correct(self):
        user = UserFactory()
        user.is_staff = False
        user.save()
        # Should not raise, no change
        update_is_staff(None, user)
        user.refresh_from_db()
        self.assertFalse(user.is_staff)


class TestStripHtmlAndNerfUrls(TestCase):
    def test_removes_html_tags(self):
        result = strip_html_and_nerf_urls("<b>Hello</b>")
        self.assertNotIn("<b>", result)
        self.assertNotIn("</b>", result)
        self.assertIn("Hello", result)

    def test_removes_colons(self):
        result = strip_html_and_nerf_urls("https://example.com")
        self.assertNotIn(":", result)

    def test_removes_slashes(self):
        result = strip_html_and_nerf_urls("https://example.com/path")
        self.assertNotIn("/", result)

    def test_nerfs_url_in_html_attribute(self):
        result = strip_html_and_nerf_urls('<a href="https://evil.com">click</a>')
        self.assertNotIn("https", result)
        self.assertNotIn("evil.com", result)

    def test_plain_text_unchanged(self):
        result = strip_html_and_nerf_urls("Just a plain name")
        self.assertEqual(result, "Just a plain name")

    def test_empty_string(self):
        result = strip_html_and_nerf_urls("")
        self.assertEqual(result, "")
