from unittest.mock import patch

from django.test import TestCase

from ..tasks import send_mail


class TestSendEmail(TestCase):
    @patch('opentech.apply.activity.tasks.dj_send_mail')
    def test_args_passed_to_django(self, dj_send_mail):
        args = ['subject', 'message', 'from', ['to@to.com']]
        send_mail(*args)
        dj_send_mail.assert_called_once_with(*args, fail_silently=False)
