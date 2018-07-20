from django.forms.models import model_to_dict
from django.test import TestCase

from ..forms import ProfileForm
from .factories import StaffFactory, UserFactory


class BaseTestProfileForm(TestCase):
    def form_data(self, user, **values):
        fields = ProfileForm.Meta.fields
        data = model_to_dict(user, fields)
        data.update(**values)
        return data

    def submit_form(self, instance, **extra_data):
        form = ProfileForm(instance=instance, data=self.form_data(instance, **extra_data))
        if form.is_valid():
            form.save()

        return form


class TestProfileForm(BaseTestProfileForm):
    def setUp(self):
        self.user = UserFactory()

    def test_email_unique(self):
        other_user = UserFactory()
        form = self.submit_form(self.user, email=other_user.email)
        self.assertFalse(form.is_valid())
        self.user.refresh_from_db()
        self.assertNotEqual(self.user.email, other_user.email)

    def test_can_change_email(self):
        new_email = 'me@another.com'
        self.submit_form(self.user, email=new_email)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, new_email)

    def test_cant_set_slack_name(self):
        slack_name = '@foobar'
        self.submit_form(self.user, slack=slack_name)
        self.user.refresh_from_db()
        self.assertNotEqual(self.user.slack, slack_name)


class TestStaffProfileForm(BaseTestProfileForm):
    def setUp(self):
        self.staff = StaffFactory()

    def test_can_set_slack_name(self):
        slack_name = '@foobar'
        self.submit_form(self.staff, slack=slack_name)

        self.staff.refresh_from_db()
        self.assertEqual(self.staff.slack, slack_name)

    def test_can_set_slack_name_with_trailing_space(self):
        slack_name = '@foobar'
        self.submit_form(self.staff, slack=slack_name)

        self.staff.refresh_from_db()
        self.assertEqual(self.staff.slack, slack_name)

    def test_cant_set_slack_name_with_space(self):
        slack_name = '@ foobar'
        form = self.submit_form(self.staff, slack=slack_name)
        self.assertFalse(form.is_valid())

        self.staff.refresh_from_db()
        self.assertNotEqual(self.staff.slack, slack_name)

    def test_auto_prepend_at(self):
        slack_name = 'foobar'
        self.submit_form(self.staff, slack=slack_name)

        self.staff.refresh_from_db()
        self.assertEqual(self.staff.slack, '@' + slack_name)

    def test_can_clear_slack_name(self):
        slack_name = ''
        self.submit_form(self.staff, slack=slack_name)

        self.staff.refresh_from_db()
        self.assertEqual(self.staff.slack, slack_name)
