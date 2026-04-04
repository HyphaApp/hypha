"""Tests for activity/management/commands/send_staff_email_digest.py helpers."""

from django.test import SimpleTestCase, TestCase

from ..management.commands.send_staff_email_digest import (
    groupby_fund_lab_id,
    slack_message_to_markdown,
)


class TestSlackMessageToMarkdown(SimpleTestCase):
    def test_converts_slack_href_to_markdown_link(self):
        result = slack_message_to_markdown("<https://example.com|Click here>")
        self.assertEqual(result, "[Click here](https://example.com)")

    def test_no_href_unchanged(self):
        msg = "Just a plain message"
        self.assertEqual(slack_message_to_markdown(msg), msg)

    def test_multiple_hrefs_on_separate_lines_converted(self):
        # The regex is greedy so two hrefs on the same line merge into one match.
        # Each href on its own line is converted independently.
        line1 = slack_message_to_markdown("<https://a.com|A>")
        line2 = slack_message_to_markdown("<https://b.com|B>")
        self.assertEqual(line1, "[A](https://a.com)")
        self.assertEqual(line2, "[B](https://b.com)")

    def test_empty_string_returns_empty(self):
        self.assertEqual(slack_message_to_markdown(""), "")

    def test_preserves_surrounding_text(self):
        result = slack_message_to_markdown("Go to <https://x.com|here> now")
        self.assertEqual(result, "Go to [here](https://x.com) now")


class TestGroupbyFundLabId(TestCase):
    def _make_message(self, fund_id):
        """Build a minimal mock message with event.source.round chain."""
        from unittest.mock import MagicMock

        msg = MagicMock()
        # Simulate the round path: event.source.get_from_parent("id")
        # extract_fund_or_lab_property checks hasattr(event.source, "get_from_parent")
        # and then event.source.round (falsy means lab path)
        msg.event.source.round = None  # lab path → get_from_parent("id")
        msg.event.source.get_from_parent.return_value = fund_id
        return msg

    def test_groups_messages_by_fund_id(self):
        msg1 = self._make_message(1)
        msg2 = self._make_message(1)
        msg3 = self._make_message(2)
        items = dict(groupby_fund_lab_id([msg1, msg2, msg3]))
        self.assertEqual(len(items[1]), 2)
        self.assertEqual(len(items[2]), 1)

    def test_message_without_fund_id_excluded(self):
        msg = self._make_message(None)
        items = dict(groupby_fund_lab_id([msg]))
        self.assertEqual(items, {})

    def test_empty_list_returns_empty(self):
        items = dict(groupby_fund_lab_id([]))
        self.assertEqual(items, {})

    def test_single_message_grouped(self):
        msg = self._make_message(42)
        items = dict(groupby_fund_lab_id([msg]))
        self.assertIn(42, items)
        self.assertEqual(len(items[42]), 1)
