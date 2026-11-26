from unittest import mock

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import RequestFactory, TestCase, override_settings

from ..models import PendingSignup
from ..utils import (
    email_comparison_key,
    emails_match,
    filter_by_email,
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
        assert "https://primary-test-host.org/account/activate/" in email_body

    def test_activation_email_points_to_passwordless_login(self):
        send_activation_email(UserFactory())
        email_body = mail.outbox[0].body
        assert "log in at: https://primary-test-host.org/auth/" in email_body
        assert "no password needed" in email_body

    def test_activation_email_is_not_html_escaped(self):
        send_activation_email(
            UserFactory(full_name="Anna O'Brien"), redirect_url="/apply/?a=1&b=2"
        )
        email_body = mail.outbox[0].body
        assert "Dear Anna O'Brien," in email_body
        assert "?next=/apply/?a=1&b=2" in email_body

    def test_set_password_email_is_not_html_escaped(self):
        send_activation_email(
            UserFactory(full_name="Anna O'Brien"),
            email_template="users/emails/set_password.txt",
            email_subject_template="users/emails/set_password_subject.txt",
            redirect_url="/apply/?a=1&b=2",
        )
        email_body = mail.outbox[0].body
        assert "Dear Anna O'Brien," in email_body
        assert "?next=/apply/?a=1&b=2" in email_body


class TestEmailComparison(TestCase):
    def test_key_lowercases_whole_address(self):
        assert email_comparison_key("Bob.Smith@Example.COM") == "bob.smith@example.com"

    def test_key_strips_whitespace(self):
        assert email_comparison_key(" Bill@gmail.com\n") == "bill@gmail.com"
        assert emails_match(" bill@gmail.com", "bill@gmail.com")

    def test_key_case_folds(self):
        # Same as Django's `_unicode_ci_compare`, casefold() maps "ß" to "ss".
        assert email_comparison_key("Straße@example.de") == "strasse@example.de"

    def test_key_of_empty_value(self):
        assert email_comparison_key(None) == ""
        assert email_comparison_key("") == ""

    def test_match_ignores_case(self):
        assert emails_match("Bob@Example.com", "bob@EXAMPLE.com")

    def test_match_normalizes_unicode(self):
        # Fullwidth letters fold to their base letters under NFKC.
        assert emails_match("ｂｏｂ@example.com", "bob@example.com")
        # Composed and decomposed "é" are the same address.
        assert emails_match("jos\u00e9@example.com", "jose\u0301@example.com")
        # Non-ASCII letters are lowercased too.
        assert emails_match("ÅSA@example.se", "åsa@example.se")

    def test_lookalikes_do_not_match(self):
        # Dotless i, dotted capital I and Cyrillic a are different letters.
        assert not emails_match("bob@gmail.com", "bob@gma\u0131l.com")
        assert not emails_match("bob@gmail.com", "bob@gma\u0130l.com")
        assert not emails_match("bob@gmail.com", "bob@gm\u0430il.com")

    def test_empty_values_never_match(self):
        assert not emails_match(None, None)
        assert not emails_match("", "")
        assert not emails_match("bob@example.com", None)


class TestFilterByEmail(TestCase):
    def test_matches_case_variants(self):
        user1 = UserFactory(email="bob@example.com")
        users = get_user_model().objects.all()

        assert list(filter_by_email(users, "Bob@Example.COM")) == [user1]

    def test_matches_stored_non_ascii_capitals_typed_as_stored(self):
        user1 = UserFactory(email="ÅSA@example.se")
        users = get_user_model().objects.all()

        assert list(filter_by_email(users, "ÅSA@example.se")) == [user1]

    def test_lookalikes_are_not_matched(self):
        # PostgreSQL UPPER('ı') is 'I' under UTF-8 locales, so an `iexact`
        # lookup would treat these as the same address.
        dotless = UserFactory(email="bob@gma\u0131l.com")
        dotted = UserFactory(email="bob@gma\u0130l.com")
        users = get_user_model().objects.all()

        assert not filter_by_email(users, "bob@gmail.com").exists()
        assert list(filter_by_email(users, "bob@gma\u0131l.com")) == [dotless]
        assert list(filter_by_email(users, "bob@gma\u0130l.com")) == [dotted]

    def test_matches_with_surrounding_whitespace(self):
        user1 = UserFactory(email="bill@gmail.com")
        users = get_user_model().objects.all()

        assert list(filter_by_email(users, " bill@gmail.com")) == [user1]

    def test_empty_email_matches_nothing(self):
        UserFactory()
        users = get_user_model().objects.all()

        assert not filter_by_email(users, "").exists()
        assert not filter_by_email(users, "   ").exists()
        assert not filter_by_email(users, None).exists()

    def test_database_matches_are_checked_in_python(self):
        # Whether `iexact` gives a false match like "ı" == "i" depends on the
        # database locale, so check that every candidate goes through
        # emails_match.
        UserFactory(email="bob@example.com")
        users = get_user_model().objects.all()

        with mock.patch(
            "hypha.apply.users.utils.emails_match", return_value=False
        ) as emails_match_mock:
            assert not filter_by_email(users, "bob@example.com").exists()
        emails_match_mock.assert_called_once_with("bob@example.com", "bob@example.com")

    def test_other_field(self):
        signup = PendingSignup.objects.create(email="New@Example.com", token="x")

        assert (
            filter_by_email(PendingSignup.objects.all(), "new@example.com").get()
            == signup
        )


class TestGetUserByEmail(TestCase):
    def test_no_account(self):
        assert get_user_by_email(email="abc@gmail.com") is None

    def test_single_same_email(self):
        user1 = UserFactory(email="abc@gmail.com")

        assert get_user_by_email(email="abc@gmail.com").id == user1.id
        assert get_user_by_email(email="ABC@gmail.com").id == user1.id
        assert get_user_by_email(email="ABC@GMAIL.COM").id == user1.id

    def test_surrounding_whitespace(self):
        user1 = UserFactory(email="bill@gmail.com")

        assert get_user_by_email(email=" bill@gmail.com").id == user1.id

    def test_lookalike(self):
        UserFactory(email="bob@gmail.com")

        assert get_user_by_email(email="bob@gma\u0131l.com") is None

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

    def test_surrounding_whitespace(self):
        UserFactory(email="bill@gmail.com")

        assert is_user_already_registered(email=" bill@gmail.com")[0]

    def test_lookalike(self):
        UserFactory(email="abc@gmail.com")

        assert not is_user_already_registered(email="abc@gma\u0131l.com")[0]


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
