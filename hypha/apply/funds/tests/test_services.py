from unittest.mock import patch

from django.test import TestCase

from hypha.apply.funds.services import translate_submission_form_data
from hypha.apply.funds.tests.factories import ApplicationSubmissionFactory
from hypha.apply.users.tests.factories import ApplicantFactory


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

    def test_translate_submission_form_data_plaintext_fields(self):
        uuid = "97c51cea-ab47-4a64-a64a-15d893788ef2"  # random uuid
        self.application.form_data[uuid] = "Just a plain text field"

        translated_form_data = translate_submission_form_data(
            self.application, "en", "fr"
        )

        self.assertEqual(
            translated_form_data[uuid], "ustjay away lainpay exttay ieldfay"
        )

    def test_translate_submission_form_data_html_fields(self):
        uuid_mixed_format = "ed89378g-3b54-4444-abcd-37821f58ed89"  # random uuid
        self.application.form_data[uuid_mixed_format] = (
            "<p>Hello from a <em>Hyper Text Markup Language</em> field</p>"
        )

        uuid_same_format = "9191fc65-02c6-46e0-9fc8-3b778113d19f"  # random uuid
        self.application.form_data[uuid_same_format] = (
            "<p><strong>Hypha rocks</strong></p><p>yeah</p>"
        )

        translated_form_data = translate_submission_form_data(
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

    def test_translate_submission_form_data_skip_info_fields(self):
        self.application.form_data["random"] = "don't translate me pls"

        name = self.form_data["full_name"]
        email = self.form_data["email"]
        random = self.form_data["random"]

        translated_form_data = translate_submission_form_data(
            self.application, "en", "fr"
        )
        self.assertEqual(translated_form_data["full_name"], name)
        self.assertEqual(translated_form_data["email"], email)
        self.assertEqual(translated_form_data["random"], random)

    def test_translate_submission_form_data_skip_non_str_fields(self):
        uuid = "4716ddd4-ce87-4964-b82d-bf2db75bdbc3"  # random uuid
        self.application.form_data[uuid] = {"test": "dict field"}

        translated_form_data = translate_submission_form_data(
            self.application, "en", "fr"
        )
        self.assertEqual(translated_form_data[uuid], {"test": "dict field"})

    def test_translate_submission_form_data_error_bubble_up(self):
        """Ensure errors bubble up from underlying translate func"""
        application = ApplicationSubmissionFactory()
        with self.assertRaises(ValueError):
            # duplicate language code
            translate_submission_form_data(application, "en", "en")

        with self.assertRaises(ValueError):
            # language code not in `mocked_translate`
            translate_submission_form_data(application, "de", "en")
