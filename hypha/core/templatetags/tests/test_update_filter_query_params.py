"""Tests for update_filter_query_params template tag."""

from django.test import SimpleTestCase
from django.test.client import RequestFactory

from hypha.core.templatetags.querystrings import update_filter_query_params


class TestUpdateFilterQueryParams(SimpleTestCase):
    factory = RequestFactory()

    def _ctx(self, qs=""):
        return {"request": self.factory.get(f"/test/{qs}")}

    def test_remove_single_value(self):
        ctx = self._ctx("?status=open&status=closed")
        result = update_filter_query_params(ctx, "status", "open", operation="remove")
        self.assertNotIn("status=open", result)
        self.assertIn("status=closed", result)

    def test_remove_last_value_drops_key(self):
        ctx = self._ctx("?status=open")
        result = update_filter_query_params(ctx, "status", "open", operation="remove")
        self.assertNotIn("status", result)

    def test_modify_replaces_value(self):
        ctx = self._ctx("?page=1")
        result = update_filter_query_params(ctx, "page", "2", operation="modify")
        self.assertIn("page=2", result)
        self.assertNotIn("page=1", result)

    def test_add_appends_new_value(self):
        ctx = self._ctx("?status=open")
        result = update_filter_query_params(ctx, "status", "closed", operation="add")
        self.assertIn("status=open", result)
        self.assertIn("status=closed", result)

    def test_add_does_not_duplicate_existing_value(self):
        ctx = self._ctx("?status=open")
        result = update_filter_query_params(ctx, "status", "open", operation="add")
        # Should appear exactly once
        self.assertEqual(result.count("status=open"), 1)

    def test_add_returns_only_query_string(self):
        ctx = self._ctx("?x=1")
        result = update_filter_query_params(ctx, "x", "2", operation="add")
        self.assertTrue(result.startswith("?"))
        self.assertNotIn("/test/", result)

    def test_remove_default_operation(self):
        ctx = self._ctx("?a=1")
        result = update_filter_query_params(ctx, "a", "1")
        self.assertNotIn("a=1", result)

    def test_modify_on_empty_query_adds_key(self):
        ctx = self._ctx()
        result = update_filter_query_params(ctx, "page", "3", operation="modify")
        self.assertIn("page=3", result)
