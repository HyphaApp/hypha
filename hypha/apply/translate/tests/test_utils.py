import json
from typing import Optional
from unittest import skipUnless
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlparse

from django.conf import settings
from django.http import QueryDict
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings

from hypha.apply.funds.tests.factories import ApplicationSubmissionFactory
from hypha.apply.users.tests.factories import ApplicantFactory

if settings.APPLICATION_TRANSLATIONS_ENABLED:
    from hypha.apply.translate.utils import (
        get_available_translations,
        get_lang_name,
        get_language_choices_json,
        get_translation_params,
        translate_application_form_data,
    )


@skipUnless(
    settings.APPLICATION_TRANSLATIONS_ENABLED,
    "Attempts to import translate dependencies",
)
class TesGetAvailableTranslations(SimpleTestCase):
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


@skipUnless(
    settings.APPLICATION_TRANSLATIONS_ENABLED,
    "Attempts to import translate dependencies",
)
class TestGetTranslationParams(SimpleTestCase):
    def get_test_get_request(self, extra_params: Optional[str] = None) -> Mock:
        extra_params = f"{extra_params}&" if extra_params else ""
        return RequestFactory().get(
            "/test/", data=QueryDict(f"{extra_params}fl=ar&tl=en")
        )

    def get_test_url(self, extra_params: Optional[str] = None) -> str:
        extra_params = f"{extra_params}&" if extra_params else ""
        return f"https://hyphaiscool.org/apply/submissions/6/?{extra_params}fl=ar&tl=en"

    def test_get_translation_params_with_request(self):
        self.assertEqual(
            get_translation_params(request=self.get_test_get_request()), ("ar", "en")
        )

        # Ensure param extraction works even when unrelated params are present
        mock_request = self.get_test_get_request(extra_params="ref=table-view")
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
            get_translation_params(self.get_test_url(), self.get_test_get_request())

    def test_get_translation_params_with_invalid_params(self):
        # Testing using params that hypha can give but are unrelated to translations
        mock_request = RequestFactory().get("/test/", data=QueryDict("ref=table-view"))
        self.assertIsNone(get_translation_params(request=mock_request))

        url = "https://hyphaiscool.org/apply/submissions/6/?ref=table-view"
        self.assertIsNone(get_translation_params(url=url))


@skipUnless(
    settings.APPLICATION_TRANSLATIONS_ENABLED,
    "Attempts to import translate dependencies",
)
class TestGetLangName(SimpleTestCase):
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


@skipUnless(
    settings.APPLICATION_TRANSLATIONS_ENABLED,
    "Attempts to import translate dependencies",
)
class TestTranslateSubmissionFormData(TestCase):
    @staticmethod
    def mocked_translate(string: str, from_code, to_code):
        """Use pig latin for all test translations - ie. 'hypha is cool' -> 'yphahay isway oolcay'
        https://en.wikipedia.org/wiki/Pig_Latin
        """
        valid_codes = ["en", "fr", "zh", "es"]
        if from_code == to_code or not (
            from_code in valid_codes and to_code in valid_codes
        ):
            raise ValueError()

        vowels = {"a", "e", "i", "o", "u"}
        string = string.lower()
        pl = [
            f"{word}way" if word[0] in vowels else f"{word[1:]}{word[0]}ay"
            for word in string.split()
        ]
        return " ".join(pl)

    @classmethod
    def setUpClass(cls):
        """Used to patch & mock all the methods called from hypha.apply.translate"""
        cls.patcher = patch(
            "hypha.apply.translate.translate.translate",
            side_effect=cls.mocked_translate,
        )
        cls.patcher.start()

    @classmethod
    def tearDownClass(cls):
        cls.patcher.stop()

    def setUp(self):
        self.applicant = ApplicantFactory(
            email="test@hyphaiscool.com", full_name="Johnny Doe"
        )
        self.application = ApplicationSubmissionFactory(user=self.applicant)

    @property
    def form_data(self):
        return self.application.live_revision.form_data

    def test_translate_application_form_data_plaintext_fields(self):
        uuid = "97c51cea-ab47-4a64-a64a-15d893788ef2"  # random uuid
        self.application.form_data[uuid] = "Just a plain text field"

        translated_form_data = translate_application_form_data(
            self.application, "en", "fr"
        )

        self.assertEqual(
            translated_form_data[uuid], "ustjay away lainpay exttay ieldfay"
        )

    def test_translate_application_form_data_html_fields(self):
        uuid_mixed_format = "ed89378g-3b54-4444-abcd-37821f58ed89"  # random uuid
        self.application.form_data[uuid_mixed_format] = (
            "<p>Hello from a <em>Hyper Text Markup Language</em> field</p>"
        )

        uuid_same_format = "9191fc65-02c6-46e0-9fc8-3b778113d19f"  # random uuid
        self.application.form_data[uuid_same_format] = (
            "<p><strong>Hypha rocks</strong></p><p>yeah</p>"
        )

        translated_form_data = translate_application_form_data(
            self.application, "en", "fr"
        )

        self.assertEqual(
            translated_form_data[uuid_mixed_format],
            "<p>ellohay romfay away yperhay exttay arkupmay anguagelay ieldfay</p>",
        )
        self.assertEqual(
            translated_form_data[uuid_same_format],
            "<p><strong>yphahay ocksray</strong></p><p>eahyay</p>",
        )

    def test_translate_application_form_data_skip_info_fields(self):
        self.application.form_data["random"] = "don't translate me pls"

        name = self.form_data["full_name"]
        email = self.form_data["email"]
        random = self.form_data["random"]

        translated_form_data = translate_application_form_data(
            self.application, "en", "fr"
        )
        self.assertEqual(translated_form_data["full_name"], name)
        self.assertEqual(translated_form_data["email"], email)
        self.assertEqual(translated_form_data["random"], random)

    def test_translate_application_form_data_skip_non_str_fields(self):
        uuid = "4716ddd4-ce87-4964-b82d-bf2db75bdbc3"  # random uuid
        self.application.form_data[uuid] = {"test": "dict field"}

        translated_form_data = translate_application_form_data(
            self.application, "en", "fr"
        )
        self.assertEqual(translated_form_data[uuid], {"test": "dict field"})

    def test_translate_application_form_data_error_bubble_up(self):
        """Ensure errors bubble up from underlying translate func"""
        application = ApplicationSubmissionFactory()
        with self.assertRaises(ValueError):
            # duplicate language code
            translate_application_form_data(application, "en", "en")

        with self.assertRaises(ValueError):
            # language code not in `mocked_translate`
            translate_application_form_data(application, "de", "en")


# Setup for testing `get_language_choices_json`


def equal_ignore_order(a: list, b: list) -> bool:
    """Used to compare two lists that are unsortable & unhashable

    Primarily used when comparing the result of json.loads

    Args:
        a: the first unhashable & unsortable list
        b: the second unhashable & unsortable list

    Returns:
        bool: true when lists are equal in length & content
    """
    if len(a) != len(b):
        return False
    unmatched = list(b)
    for element in a:
        try:
            unmatched.remove(element)
        except ValueError:
            return False
    return not unmatched


@skipUnless(
    settings.APPLICATION_TRANSLATIONS_ENABLED,
    "Attempts to import translate dependencies",
)
class TestGetLanguageChoices(SimpleTestCase):
    @staticmethod
    def mocked_get_lang_name(code):
        # Added "!" to ensure the mock is being called rather than the actual get_lang
        codes_to_lang = {
            "en": "English!",
            "ar": "Arabic!",
            "zh": "Chinese!",
            "fr": "French!",
        }
        return codes_to_lang[code]

    @staticmethod
    def mocked_get_translation_params(url):
        query_dict = {k: v[0] for (k, v) in parse_qs(urlparse(url).query).items()}
        if (to_lang := query_dict.get("tl")) and (from_lang := query_dict.get("fl")):
            return (from_lang, to_lang)

    @classmethod
    def setUpClass(cls):
        """Used to patch & mock all the methods called from hypha.apply.translate.utils"""
        available_packages = [
            Mock(from_code="ar", to_code="en"),
            Mock(from_code="fr", to_code="en"),
            Mock(from_code="en", to_code="ar"),
            Mock(from_code="zh", to_code="en"),
            Mock(from_code="en", to_code="fr"),
        ]

        cls.patcher = [
            patch(
                "hypha.apply.translate.utils.get_lang_name",
                side_effect=cls.mocked_get_lang_name,
            ),
            patch(
                "hypha.apply.translate.utils.get_available_translations",
                return_value=available_packages,
            ),
            patch(
                "hypha.apply.translate.utils.get_translation_params",
                side_effect=cls.mocked_get_translation_params,
            ),
        ]

        for patched in cls.patcher:
            patched.start()

    @classmethod
    def tearDownClass(cls):
        for patched in cls.patcher:
            patched.stop()

    def test_get_language_choices_json(self):
        expected_json = [
            {
                "label": "English!",
                "selected": False,
                "to": [
                    {"label": "Arabic!", "selected": True, "value": "ar"},
                    {"label": "French!", "selected": False, "value": "fr"},
                ],
                "value": "en",
            },
            {
                "label": "Arabic!",
                "selected": False,
                "to": [{"label": "English!", "selected": True, "value": "en"}],
                "value": "ar",
            },
            {
                "label": "Chinese!",
                "selected": False,
                "to": [{"label": "English!", "selected": True, "value": "en"}],
                "value": "zh",
            },
            {
                "label": "French!",
                "selected": False,
                "to": [{"label": "English!", "selected": True, "value": "en"}],
                "value": "fr",
            },
        ]
        request = RequestFactory().get("/test/")

        json_out = get_language_choices_json(request)
        self.assertTrue(equal_ignore_order(json.loads(json_out), expected_json))

    def test_get_language_choices_json_with_current_url(self):
        expected_json = [
            {
                "label": "English!",
                "selected": False,
                "to": [
                    {"label": "Arabic!", "selected": True, "value": "ar"},
                    {"label": "French!", "selected": False, "value": "fr"},
                ],
                "value": "en",
            },
            {
                "label": "Arabic!",
                "selected": True,
                "to": [{"label": "English!", "selected": True, "value": "en"}],
                "value": "ar",
            },
            {
                "label": "Chinese!",
                "selected": False,
                "to": [{"label": "English!", "selected": True, "value": "en"}],
                "value": "zh",
            },
            {
                "label": "French!",
                "selected": False,
                "to": [{"label": "English!", "selected": True, "value": "en"}],
                "value": "fr",
            },
        ]
        current_url = "https://hyphaiscool.org/apply/submissions/6/?fl=ar&tl=en"
        request = RequestFactory().get(
            "/test/", headers={"Hx-Current-Url": current_url}
        )

        json_out = get_language_choices_json(request)
        self.assertTrue(equal_ignore_order(json.loads(json_out), expected_json))

    @override_settings(LANGUAGE_CODE="fr")
    def test_get_language_choices_json_with_language_code(self):
        expected_json = [
            {
                "label": "English!",
                "selected": False,
                "to": [
                    {"label": "Arabic!", "selected": False, "value": "ar"},
                    {"label": "French!", "selected": True, "value": "fr"},
                ],
                "value": "en",
            },
            {
                "label": "Arabic!",
                "selected": False,
                "to": [{"label": "English!", "selected": True, "value": "en"}],
                "value": "ar",
            },
            {
                "label": "Chinese!",
                "selected": False,
                "to": [{"label": "English!", "selected": True, "value": "en"}],
                "value": "zh",
            },
            {
                "label": "French!",
                "selected": False,
                "to": [{"label": "English!", "selected": True, "value": "en"}],
                "value": "fr",
            },
        ]
        request = RequestFactory().get("/test/")

        json_out = get_language_choices_json(request)
        self.assertTrue(equal_ignore_order(json.loads(json_out), expected_json))
