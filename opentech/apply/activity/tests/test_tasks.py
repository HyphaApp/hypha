from unittest.mock import patch

from django.test import TestCase

from ..tasks import send_mail

from .factories import MessageFactory


class TestSendEmail(TestCase):
    @patch('opentech.apply.activity.tasks.EmailMessage', autospec=True)
    def test_args_passed_to_django(self, email_mock):
        kwargs = {
            'subject': 'subject',
            'body': 'body',
            'from_email': 'from_email',
            'to': 'to',
        }
        send_mail(*kwargs, log=MessageFactory())
        email_mock.assert_called_once_with(**kwargs)
