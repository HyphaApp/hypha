"""Tests for core/navigation.py pure helper functions."""

from django.test import SimpleTestCase

from hypha.core.navigation import _calculate_is_active, _check_permission


class TestCalculateIsActive(SimpleTestCase):
    def test_exact_url_match_returns_true(self):
        self.assertTrue(_calculate_is_active("/dashboard/", None, "/dashboard/"))

    def test_different_url_returns_false(self):
        self.assertFalse(_calculate_is_active("/dashboard/", None, "/submissions/"))

    def test_regex_match_returns_true(self):
        self.assertTrue(
            _calculate_is_active(
                "/other/",
                r"^/submissions/",
                "/submissions/all/",
            )
        )

    def test_regex_no_match_returns_false(self):
        self.assertFalse(
            _calculate_is_active(
                "/other/",
                r"^/submissions/",
                "/dashboard/",
            )
        )

    def test_no_regex_and_no_match_returns_false(self):
        self.assertFalse(_calculate_is_active("/a/", None, "/b/"))

    def test_regex_takes_priority_over_url_mismatch(self):
        # url doesn't match, but regex does
        self.assertTrue(_calculate_is_active("/x/", r"^/y/", "/y/anything"))


class TestCheckPermission(SimpleTestCase):
    def test_invalid_module_path_returns_false(self):
        self.assertFalse(_check_permission(object(), "nonexistent.module.func"))

    def test_invalid_method_name_returns_false(self):
        self.assertFalse(
            _check_permission(object(), "hypha.core.navigation.no_such_fn")
        )

    def test_missing_dot_in_path_returns_false(self):
        self.assertFalse(_check_permission(object(), "nodot"))

    def test_function_returning_false_returns_false(self):
        # Use a known callable that returns False for any user
        # hypha.apply.users.decorators.is_apply_staff checks user.is_apply_staff
        from unittest.mock import MagicMock

        user = MagicMock()
        user.is_apply_staff = False
        result = _check_permission(user, "hypha.apply.users.decorators.is_apply_staff")
        self.assertFalse(result)

    def test_function_returning_true_returns_true(self):
        from unittest.mock import MagicMock

        user = MagicMock()
        user.is_apply_staff = True
        result = _check_permission(user, "hypha.apply.users.decorators.is_apply_staff")
        self.assertTrue(result)
