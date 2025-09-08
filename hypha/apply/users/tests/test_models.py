from django.test import TestCase
from django.utils import translation

from hypha.apply.users.tests.factories import StaffFactory


class UserModelTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = StaffFactory()

    # Requires compiling the translations first:
    # uv run --with-requirements=requirements/dev.txt python -m django compilemessages --ignore=.venv/* --locale=ru
    def test_is_apply_staff(self):
        self.assertTrue(self.user.is_apply_staff)
        translation.activate("ru")
        del self.user.is_apply_staff  # Clear cached value
        self.assertTrue(self.user.is_apply_staff)
