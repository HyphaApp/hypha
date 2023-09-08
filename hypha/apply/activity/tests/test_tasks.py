from unittest.mock import patch

from django.test import TestCase

from ..tasks import send_mail
from .factories import MessageFactory


class TestSendEmail(TestCase):
    @patch("hypha.apply.activity.tasks.EmailMessage", autospec=True)
    def test_args_passed_to_django(self, email_mock):
        kwargs = {
            "subject": "subject",
            "body": "body",
            "from_email": "from_email",
            "to": "to",
        }
        with self.settings(EMAIL_SUBJECT_PREFIX=""):
            send_mail(*kwargs, logs=[MessageFactory()])
            email_mock.assert_called_once_with(**kwargs)

        with self.settings(EMAIL_SUBJECT_PREFIX="[PREFIX] "):
            send_mail(*kwargs, logs=[MessageFactory()])
            kwargs["subject"] = "[PREFIX] subject"
            email_mock.assert_called_with(**kwargs)
