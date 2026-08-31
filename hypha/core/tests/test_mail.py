"""Tests for core/mail.py helper functions."""

from django.test import SimpleTestCase
from django.utils import translation

from hypha.core.mail import language, remove_extra_empty_lines


class TestRemoveExtraEmptyLines(SimpleTestCase):
    def test_consecutive_blank_lines_collapsed(self):
        text = "line1\n\nline2"
        result = remove_extra_empty_lines(text)
        self.assertNotIn("\n\n", result)

    def test_blank_line_with_spaces_collapsed(self):
        text = "a\n   \nb"
        result = remove_extra_empty_lines(text)
        self.assertNotIn("\n   \n", result)

    def test_single_newline_unchanged(self):
        text = "line1\nline2"
        result = remove_extra_empty_lines(text)
        self.assertIn("line1", result)
        self.assertIn("line2", result)

    def test_empty_string_unchanged(self):
        self.assertEqual(remove_extra_empty_lines(""), "")

    def test_no_blank_lines_unchanged(self):
        text = "Hello World"
        self.assertEqual(remove_extra_empty_lines(text), text)


class TestLanguageContextManager(SimpleTestCase):
    def test_activates_language_inside_block(self):
        with language("fr"):
            self.assertEqual(translation.get_language(), "fr")

    def test_restores_original_language_after_block(self):
        original = translation.get_language()
        with language("de"):
            pass
        self.assertEqual(translation.get_language(), original)

    def test_restores_language_on_exception(self):
        original = translation.get_language()
        try:
            with language("es"):
                raise ValueError("oops")
        except ValueError:
            pass
        self.assertEqual(translation.get_language(), original)
