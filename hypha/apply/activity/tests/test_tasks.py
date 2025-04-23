from unittest.mock import patch

from django.test import SimpleTestCase, TestCase

from ..tasks import send_mail_task, update_message_status
from .factories import MessageFactory


class TestSendEmail(SimpleTestCase):
    @patch("hypha.apply.activity.tasks.EmailMessage", autospec=True)
    def test_args_passed_to_django(self, email_mock):
        kwargs = {
            "subject": "subject",
            "body": "this is my super cool email that celery is sending",
            "from_email": "from_email",
            "to": ["test@hyphaiscool.com"],
        }

        response = send_mail_task.apply(kwargs=kwargs).result

        email_mock.assert_called_once_with(**kwargs)
        self.assertEqual(response["status"], "sent")

    @patch(
        "hypha.apply.activity.tasks.EmailMessage.send",
        side_effect=Exception("this is an error"),
    )
    def test_email_failed_status_updated(self, fail_mock):
        kwargs = {
            "subject": "subject",
            "body": "this is my super cool email that celery is sending",
            "from_email": "from_email",
            "to": ["test@hyphaiscool.com"],
        }

        response = send_mail_task.apply(kwargs=kwargs).result

        fail_mock.assert_called_once()
        self.assertEqual(response["status"], "Error: this is an error")


class TestUpdateMessageStatus(TestCase):
    def test_message_status_updated(self):
        response = {"status": "sent", "id": None}

        message = MessageFactory()

        kwargs = {
            "response": response,
            "message_pks": [message.id],
        }

        update_message_status.apply(kwargs=kwargs)

        message.refresh_from_db()

        self.assertEqual(message.status, "sent")
