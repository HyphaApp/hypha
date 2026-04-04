"""Tests for funds/differ.py."""

from django.test import SimpleTestCase

from ..differ import compare, wrap_added, wrap_deleted


class TestWrapDeleted(SimpleTestCase):
    def test_wraps_text_in_del_tag(self):
        result = wrap_deleted("hello")
        self.assertIn("<del>", result)
        self.assertIn("</del>", result)
        self.assertIn("hello", result)


class TestWrapAdded(SimpleTestCase):
    def test_wraps_text_in_ins_tag(self):
        result = wrap_added("world")
        self.assertIn("<ins>", result)
        self.assertIn("</ins>", result)
        self.assertIn("world", result)


class TestCompare(SimpleTestCase):
    def test_identical_strings_have_no_diff_markers(self):
        a, b = compare("hello world", "hello world")
        self.assertNotIn("<del>", a)
        self.assertNotIn("<ins>", b)
        self.assertIn("hello world", a)

    def test_added_text_wrapped_in_ins(self):
        a, b = compare("hello", "hello world")
        self.assertNotIn("<ins>", a)
        self.assertIn("<ins>", b)

    def test_deleted_text_wrapped_in_del(self):
        a, b = compare("hello world", "hello")
        self.assertIn("<del>", a)
        self.assertNotIn("<del>", b)

    def test_replaced_text_shows_del_and_ins(self):
        a, b = compare("foo", "bar")
        self.assertIn("<del>", a)
        self.assertIn("<ins>", b)

    def test_returns_tuple_of_two(self):
        result = compare("a", "b")
        self.assertEqual(len(result), 2)

    def test_html_stripped_when_should_clean_true(self):
        # HTML tags should be stripped when should_clean=True (default)
        a, b = compare("<b>hello</b>", "<b>hello</b>")
        self.assertNotIn("<b>", a)
        self.assertNotIn("<b>", b)

    def test_html_preserved_when_should_clean_false(self):
        a, b = compare("<b>hello</b>", "<b>hello</b>", should_clean=False)
        self.assertIn("<b>", a)
        self.assertIn("<b>", b)

    def test_empty_strings(self):
        a, b = compare("", "")
        self.assertEqual(str(a), "")
        self.assertEqual(str(b), "")

    def test_paragraph_break_inserted_after_period_newline(self):
        # ".\n" should become ".\n<br><br>" in output
        a, b = compare("sentence.\nNext", "sentence.\nNext", should_clean=False)
        self.assertIn("<br><br>", a)

    def test_li_tag_replaced_with_bullet_character(self):
        # "<li>" prefixed items should get "◦ " prepended → then converted to <br>◦
        a, b = compare("<li>item</li>", "<li>item</li>")
        self.assertIn("◦", a)

    def test_empty_vs_nonempty(self):
        a, b = compare("", "new content")
        self.assertEqual(str(a), "")
        self.assertIn("<ins>", b)

    def test_nonempty_vs_empty(self):
        a, b = compare("old content", "")
        self.assertIn("<del>", a)
        self.assertEqual(str(b), "")
