from typing import List
from unittest import skipUnless
from unittest.mock import Mock, patch

from django.conf import settings
from django.test import SimpleTestCase

if settings.APPLICATION_TRANSLATIONS_ENABLED:
    from hypha.apply.translate.translate import translate


@skipUnless(
    settings.APPLICATION_TRANSLATIONS_ENABLED,
    "Attempts to import translate dependencies",
)
class TestTranslate(SimpleTestCase):
    @staticmethod
    def mocked_translate(string: str, from_code, to_code):
        """Use pig latin for all test translations - ie. 'hypha is cool' -> 'yphahay isway oolcay'
        https://en.wikipedia.org/wiki/Pig_Latin
        """
        vowels = {"a", "e", "i", "o", "u"}
        string = string.lower()
        pl = [
            f"{word}way" if word[0] in vowels else f"{word[1:]}{word[0]}ay"
            for word in string.split()
        ]
        return " ".join(pl)

    @staticmethod
    def mocked_get_available_translations(codes: List[str]):
        mocked_packages = [
            Mock(from_code="ar", to_code="en"),
            Mock(from_code="fr", to_code="en"),
            Mock(from_code="en", to_code="ar"),
            Mock(from_code="zh", to_code="en"),
            Mock(from_code="en", to_code="fr"),
        ]

        return list(filter(lambda x: x.from_code in codes, mocked_packages))

    @classmethod
    def setUpClass(cls):
        """Used to patch & mock all the methods called from argostranslate & hypha.apply.translate.utils"""

        cls.patcher = [
            patch(
                "hypha.apply.translate.utils.get_available_translations",
                side_effect=cls.mocked_get_available_translations,
            ),
            patch(
                "argostranslate.translate.translate", side_effect=cls.mocked_translate
            ),
        ]

        for patched in cls.patcher:
            patched.start()

    @classmethod
    def tearDownClass(cls):
        for patched in cls.patcher:
            patched.stop()

    def test_valid_translate(self):
        self.assertEqual(translate("hey there", "fr", "en"), "eyhay heretay")

    def test_duplicate_code_translate(self):
        with self.assertRaises(ValueError) as context:
            translate("hey there", "fr", "fr")

        self.assertEqual(
            "Translation from_code cannot match to_code", str(context.exception)
        )

    def test_invalid_code_translate(self):
        with self.assertRaises(ValueError) as context:
            translate("hey there", "test", "test2")

        self.assertIn("is not installed", str(context.exception))
