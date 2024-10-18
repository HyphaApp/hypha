import json
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlparse

import pytest
from django.test import TestCase, override_settings
from freezegun import freeze_time

from hypha.apply.funds.utils import get_copied_form_name, get_language_choices_json

date = "2024-10-16 15:05:13.721861"

form_name_dataset = [
    ("Test Form", "Test Form (Copied on 2024-10-16 15:05:13.72)"),
    (
        "A Copied Form! (Copied on 2022-09-25 16:30:26.04)",
        "A Copied Form! (Copied on 2024-10-16 15:05:13.72)",
    ),
    (
        "(Copied on 2020-10-30 18:13:26.04) Out of place timestamp",
        "(Copied on 2020-10-30 18:13:26.04) Out of place timestamp (Copied on 2024-10-16 15:05:13.72)",
    ),
]


@freeze_time(date)
@pytest.mark.parametrize("original_name,expected", form_name_dataset)
def test_get_copied_form_name(original_name, expected):
    assert get_copied_form_name(original_name) == expected


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


class TestGetLanguageChoices(TestCase):
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
        request = Mock(headers={})

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
        request = Mock(headers={"Hx-Current-Url": current_url})

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
        request = Mock(headers={})

        json_out = get_language_choices_json(request)
        self.assertTrue(equal_ignore_order(json.loads(json_out), expected_json))
