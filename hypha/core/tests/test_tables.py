"""Tests for core/tables.py."""

from datetime import datetime, timezone

from django.test import SimpleTestCase

from hypha.core.tables import RelativeTimeColumn


class TestRelativeTimeColumn(SimpleTestCase):
    def setUp(self):
        self.col = RelativeTimeColumn()

    def test_none_value_returns_dash(self):
        self.assertEqual(self.col.render(None), "—")

    def test_empty_string_returns_dash(self):
        self.assertEqual(self.col.render(""), "—")

    def test_renders_relative_time_element(self):
        dt = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        result = str(self.col.render(dt))
        self.assertIn("<relative-time", result)
        self.assertIn("</relative-time>", result)

    def test_renders_iso_datetime_attribute(self):
        dt = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        result = str(self.col.render(dt))
        self.assertIn(dt.isoformat(), result)

    def test_default_prefix_is_empty(self):
        dt = datetime(2024, 1, 1, tzinfo=timezone.utc)
        result = str(self.col.render(dt))
        self.assertIn("prefix=''", result)

    def test_custom_prefix_included(self):
        col = RelativeTimeColumn(prefix="Updated")
        dt = datetime(2024, 1, 1, tzinfo=timezone.utc)
        result = str(col.render(dt))
        self.assertIn("prefix='Updated'", result)
