from django.test import SimpleTestCase
from django.utils import translation

from hypha.apply.utils.templatetags.apply_tags import an_or_a, with_indefinite_article


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


class TestWithIndefiniteArticle(SimpleTestCase):
    def test_english_gets_an_article(self):
        with translation.override("en"):
            self.assertEqual("an invoice", with_indefinite_article("invoice"))
            self.assertEqual("a report", with_indefinite_article("report"))

    def test_english_variants_get_an_article(self):
        with translation.override("en-gb"):
            self.assertEqual("an invoice", with_indefinite_article("invoice"))

    def test_other_languages_get_the_bare_noun(self):
        # Articles are English-specific, so other languages must translate the
        # surrounding phrase rather than receive an English article.
        for language in ("sv", "fr", "zh-hans"):
            with self.subTest(language=language), translation.override(language):
                self.assertEqual("faktura", with_indefinite_article("faktura"))
