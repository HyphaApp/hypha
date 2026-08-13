from django.test import SimpleTestCase

from hypha.apply.utils.templatetags.apply_tags import an_or_a


class TestAnOrA(SimpleTestCase):
    def test_returns_an(self):
        self.assertEqual("an", an_or_a("apple"))
        self.assertEqual("an", an_or_a("invoice"))
        self.assertEqual("an", an_or_a("honor"))
        self.assertEqual("an", an_or_a("approval"))

    def test_returns_a(self):
        self.assertEqual("a", an_or_a("boy"))
        self.assertEqual("a", an_or_a("slug"))
        self.assertEqual("a", an_or_a("one"))
