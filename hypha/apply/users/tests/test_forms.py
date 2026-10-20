import pytest
from django.forms.models import model_to_dict
from django.test import RequestFactory, TestCase

from ..forms import BecomeUserForm, ProfileForm
from .factories import StaffFactory, UserFactory


class BaseTestProfileForm(TestCase):
    def form_data(self, user, **values):
        fields = ProfileForm.Meta.fields
        data = model_to_dict(user, fields)
        data.update(**values)
        return data

    def submit_form(self, instance, request=None, **extra_data):
        form = ProfileForm(
            instance=instance,
            data=self.form_data(instance, **extra_data),
            request=request,
        )
        if form.is_valid():
            form.save()

        return form


class TestProfileForm(BaseTestProfileForm):
    def setUp(self):
        self.user = UserFactory()

    def test_email_in_use_does_not_reveal_it(self):
        other_user = UserFactory()
        form = ProfileForm(
            instance=self.user, data=self.form_data(self.user, email=other_user.email)
        )
        # No "already exists" error, that would reveal the address is registered.
        # The address is checked in the email change flow instead.
        self.assertTrue(form.is_valid())

    def test_can_change_email(self):
        new_email = "me@another.com"
        self.submit_form(instance=self.user, email=new_email)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, new_email)

    def test_cant_set_slack_name(self):
        slack_name = "@foobar"
        self.submit_form(instance=self.user, slack=slack_name)
        self.user.refresh_from_db()
        self.assertNotEqual(self.user.slack, slack_name)


class TestStaffProfileForm(BaseTestProfileForm):
    def setUp(self):
        self.staff = StaffFactory()

    def test_cant_change_email_oauth(self):
        new_email = "me@this.com"
        request = RequestFactory().get("/")
        request.session = {
            "_auth_user_backend": "social_core.backends.google.GoogleOAuth2"
        }
        self.submit_form(instance=self.staff, request=request, email=new_email)
        self.staff.refresh_from_db()
        self.assertNotEqual(new_email, self.staff.email)

    def test_can_set_slack_name(self):
        slack_name = "@foobar"
        self.submit_form(instance=self.staff, slack=slack_name)

        self.staff.refresh_from_db()
        self.assertEqual(self.staff.slack, slack_name)

    def test_can_set_slack_name_with_trailing_space(self):
        self.submit_form(instance=self.staff, slack="@foobar ")

        self.staff.refresh_from_db()
        self.assertEqual(self.staff.slack, "@foobar")

    def test_cant_set_slack_name_with_space(self):
        slack_name = "@ foobar"
        form = self.submit_form(instance=self.staff, slack=slack_name)
        self.assertFalse(form.is_valid())

        self.staff.refresh_from_db()
        self.assertNotEqual(self.staff.slack, slack_name)

    def test_auto_prepend_at(self):
        slack_name = "foobar"
        self.submit_form(instance=self.staff, slack=slack_name)

        self.staff.refresh_from_db()
        self.assertEqual(self.staff.slack, "@" + slack_name)

    def test_can_clear_slack_name(self):
        slack_name = ""
        self.submit_form(instance=self.staff, slack=slack_name)

        self.staff.refresh_from_db()
        self.assertEqual(self.staff.slack, slack_name)


@pytest.mark.django_db
def test_become_user_form_query_count(django_assert_num_queries):
    # create a three user
    UserFactory(is_superuser=False)
    UserFactory(is_superuser=False)
    UserFactory(is_superuser=False)

    # Enable query counting and verify only 2 queries are made
    with django_assert_num_queries(2):
        # This should trigger 2 queries:
        # 1. Get active non-superusers
        # 2. Prefetch related groups
        form = BecomeUserForm()
        # Access choices to trigger query execution
        list(form.fields["user_pk"].choices)
