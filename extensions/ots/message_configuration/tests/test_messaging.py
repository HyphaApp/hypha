from django.core import mail
from django.test import TestCase, override_settings
from django_slack.utils import get_backend

from extensions.ots.message_configuration.models import (
    MessagingSetting,
    MessagingSettings,
)
from hypha.apply.activity.adapters import EmailAdapter, SlackAdapter
from hypha.apply.activity.options import MESSAGES
from hypha.apply.activity.tests.test_messaging import AdapterMixin
from hypha.apply.funds.tests.factories import (
    ApplicationSubmissionFactory,
)
from hypha.home.factories import ApplySiteFactory


@override_settings(SEND_MESSAGES=True)
class TestEmailMessageConfiguration(AdapterMixin, TestCase):
    source_factor = ApplicationSubmissionFactory
    adapter = EmailAdapter()

    def test_not_sent_when_default_off(self):
        apply_site = ApplySiteFactory()
        self.message_setting, _ = MessagingSetting.objects.get_or_create(
            site_id=apply_site.id,
        )
        self.message_setting.email_default_send = False
        self.message_setting.save()

        submission = ApplicationSubmissionFactory()
        self.adapter_process(MESSAGES.NEW_SUBMISSION, source=submission)
        self.assertEqual(len(mail.outbox), 0)

        self.message_setting.email_default_send = True
        self.message_setting.save()

    def test_sent_when_default_off_specific_on(self):
        apply_site = ApplySiteFactory()
        self.message_setting, _ = MessagingSetting.objects.get_or_create(
            site_id=apply_site.id,
        )
        MessagingSettings.objects.create(
            message_type=MESSAGES.NEW_SUBMISSION,
            email_enabled=True,
            slack_enabled=False,
            setting_id=self.message_setting.id,
        )
        self.message_setting.email_default_send = False
        self.message_setting.save()

        submission = ApplicationSubmissionFactory()
        self.adapter_process(MESSAGES.NEW_SUBMISSION, source=submission)
        self.assertEqual(len(mail.outbox), 1)

        self.message_setting.email_default_send = True
        self.message_setting.messaging_settings = []
        self.message_setting.save()

    def test_message_with_replacements(self):
        apply_site = ApplySiteFactory()
        self.message_setting, _ = MessagingSetting.objects.get_or_create(
            site_id=apply_site.id,
            email_header="HEADER",
            email_footer="FOOTER",
        )
        MessagingSettings.objects.create(
            message_type=MESSAGES.NEW_SUBMISSION,
            email_enabled=True,
            email_message="SUBMISSION_URL",
            slack_enabled=False,
            setting_id=self.message_setting.id,
        )
        self.message_setting.email_default_send = False
        self.message_setting.save()

        submission = ApplicationSubmissionFactory()
        self.adapter_process(MESSAGES.NEW_SUBMISSION, source=submission)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("HEADER", mail.outbox[0].body)
        self.assertIn("FOOTER", mail.outbox[0].body)
        self.assertIn("/apply/submissions", mail.outbox[0].body)

        self.message_setting.email_default_send = True
        self.message_setting.messaging_settings = []
        self.message_setting.save()


@override_settings(
    SLACK_ENDPOINT_URL="https://my-slack-backend.com/incoming/my-very-secret-key",
    SLACK_DESTINATION_ROOM="#<ROOM ID>",
    SLACK_BACKEND="django_slack.backends.TestBackend",
    SLACK_TOKEN="fake-token",
)
class TestSlackMessageConfiguration(AdapterMixin, TestCase):
    source_factor = ApplicationSubmissionFactory

    def test_not_sent_when_default_off(self):
        self.adapter = SlackAdapter()
        backend = get_backend()
        backend.reset_messages()
        apply_site = ApplySiteFactory()
        self.message_setting, _ = MessagingSetting.objects.get_or_create(
            site_id=apply_site.id,
        )
        self.message_setting.slack_default_send = False
        self.message_setting.save()

        submission = ApplicationSubmissionFactory()
        self.adapter_process(MESSAGES.NEW_SUBMISSION, source=submission)
        messages = backend.retrieve_messages()
        self.assertEqual(len(messages), 0)

        self.message_setting.slack_default_send = True
        self.message_setting.save()

    def test_sent_when_default_off_specific_on(self):
        self.adapter = SlackAdapter()
        backend = get_backend()
        backend.reset_messages()
        apply_site = ApplySiteFactory()
        self.message_setting, _ = MessagingSetting.objects.get_or_create(
            site_id=apply_site.id,
        )
        MessagingSettings.objects.create(
            message_type=MESSAGES.NEW_SUBMISSION,
            slack_enabled=True,
            email_enabled=False,
            setting_id=self.message_setting.id,
        )
        self.message_setting.slack_default_send = False
        self.message_setting.save()

        submission = ApplicationSubmissionFactory()
        self.adapter_process(MESSAGES.NEW_SUBMISSION, source=submission)
        messages = backend.retrieve_messages()
        self.assertEqual(len(messages), 1)

        self.message_setting.slack_default_send = True
        self.message_setting.messaging_settings = []
        self.message_setting.save()

    def test_message_with_replacements(self):
        self.adapter = SlackAdapter()
        backend = get_backend()
        backend.reset_messages()

        apply_site = ApplySiteFactory()
        self.message_setting, _ = MessagingSetting.objects.get_or_create(
            site_id=apply_site.id,
        )
        MessagingSettings.objects.create(
            message_type=MESSAGES.NEW_SUBMISSION,
            slack_enabled=True,
            slack_message="Testslack SUBMISSION_URL",
            email_enabled=False,
            setting_id=self.message_setting.id,
        )
        self.message_setting.email_default_send = False
        self.message_setting.save()

        submission = ApplicationSubmissionFactory()
        self.adapter_process(MESSAGES.NEW_SUBMISSION, source=submission)
        messages = backend.retrieve_messages()
        self.assertEqual(len(messages), 1)
        self.assertIn("Testslack", messages[0]["payload"])
        self.assertIn("/apply/submissions", messages[0]["payload"])

        self.message_setting.email_default_send = True
        self.message_setting.messaging_settings = []
        self.message_setting.save()
