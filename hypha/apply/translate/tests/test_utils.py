from typing import Optional
from unittest import TestCase
from unittest.mock import Mock, patch

from django.http import QueryDict

from hypha.apply.translate.utils import (
    get_available_translations,
    get_lang_name,
    get_translation_params,
)


class TesGetAvailableTranslations(TestCase):
    @classmethod
    def setUpClass(cls):
        mock_packages = [
            Mock(from_code="ar", to_code="en"),
            Mock(from_code="fr", to_code="en"),
            Mock(from_code="en", to_code="ar"),
            Mock(from_code="zh", to_code="en"),
            Mock(from_code="fr", to_code="zh"),
        ]

        cls.patcher = patch(
            "argostranslate.package.get_installed_packages", return_value=mock_packages
        )
        cls.patcher.start()

    @classmethod
    def tearDownClass(cls):
        cls.patcher.stop()

    def test_get_available_translations(self):
        codes = {(p.from_code, p.to_code) for p in get_available_translations()}
        self.assertEqual(
            codes,
            {("ar", "en"), ("fr", "en"), ("en", "ar"), ("zh", "en"), ("fr", "zh")},
        )

    def test_get_available_translations_with_codes(self):
        codes = {(p.from_code, p.to_code) for p in get_available_translations(["fr"])}
        self.assertEqual(codes, {("fr", "en"), ("fr", "zh")})

        codes = {
            (p.from_code, p.to_code) for p in get_available_translations(["en", "zh"])
        }
        self.assertEqual(codes, {("en", "ar"), ("zh", "en")})


class TestGetTranslationParams(TestCase):
    def get_test_request(self, extra_params: Optional[str] = None) -> Mock:
        extra_params = f"{extra_params}&" if extra_params else ""
        return Mock(GET=QueryDict(f"{extra_params}fl=ar&tl=en"))

    def get_test_url(self, extra_params: Optional[str] = None) -> str:
        extra_params = f"{extra_params}&" if extra_params else ""
        return f"https://hyphaiscool.org/apply/submissions/6/?{extra_params}fl=ar&tl=en"

    def test_get_translation_params_with_request(self):
        self.assertEqual(
            get_translation_params(request=self.get_test_request()), ("ar", "en")
        )

        # Ensure param extraction works even when unrelated params are present
        mock_request = self.get_test_request(extra_params="ref=table-view")
        self.assertEqual(get_translation_params(request=mock_request), ("ar", "en"))

    def test_get_translation_params_with_url(self):
        self.assertEqual(get_translation_params(url=self.get_test_url()), ("ar", "en"))

        # Ensure param extraction works even when unrelated params are present
        url = self.get_test_url("ref=table-view")
        self.assertEqual(get_translation_params(url=url), ("ar", "en"))

    def test_get_translation_params_with_invalid_args(self):
        # Should fail with no args given...
        with self.assertRaises(ValueError):
            get_translation_params()

        # ...and with both args given
        with self.assertRaises(ValueError):
            get_translation_params(self.get_test_url(), self.get_test_request())

    def test_get_translation_params_with_invalid_params(self):
        # Testing using params that hypha can give but are unrelated to translations
        mock_request = Mock(GET=QueryDict("ref=table-view"))
        self.assertIsNone(get_translation_params(request=mock_request))

        url = "https://hyphaiscool.org/apply/submissions/6/?ref=table-view"
        self.assertIsNone(get_translation_params(url=url))


class TestGetLangName(TestCase):
    def test_get_lang_name(self):
        # "!" added to ensure mock is working rather than actually calling argos
        language_mock = Mock()
        language_mock.name = (
            "Arabic!"  # Done this way as `name` is an attribute of Mock() objects
        )
        with patch(
            "argostranslate.translate.get_language_from_code",
            return_value=language_mock,
        ) as from_code_mock:
            self.assertEqual(get_lang_name("ar"), "Arabic!")
            from_code_mock.assert_called_once_with("ar")

    def test_get_lang_name_invalid_code(self):
        with patch(
            "argostranslate.translate.get_language_from_code",
            side_effect=AttributeError(),
        ) as from_code_mock:
            self.assertIsNone(get_lang_name("nope"))
            from_code_mock.assert_called_once_with("nope")
