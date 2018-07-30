import json
from unittest.mock import Mock, patch

import responses

from django.core import mail
from django.test import TestCase, override_settings
from django.contrib.messages import get_messages

from opentech.apply.utils.testing import make_request
from opentech.apply.funds.tests.factories import ApplicationSubmissionFactory
from opentech.apply.users.tests.factories import UserFactory, ReviewerFactory

from ..models import Activity
from ..messaging import (
    AdapterBase,
    ActivityAdapter,
    EmailAdapter,
    MessengerBackend,
    MESSAGES,
    SlackAdapter,
)


class TestAdapter(AdapterBase):
    """A test class which will pass the message type to send_message"""
    adapter_type = 'Test Adapter'
    messages = {
        enum: enum.value
        for enum in MESSAGES.__members__.values()
    }

    def send_message(self, message, **kwargs):
        pass

    def recipients(self, message_type, **kwargs):
        return [message_type]


@override_settings(SEND_MESSAGES=True)
class TestBaseAdapter(TestCase):
    def setUp(self):
        patched_class = patch.object(TestAdapter, 'send_message')
        self.mock_adapter = patched_class.start()
        self.adapter = TestAdapter()
        self.addCleanup(patched_class.stop)

    def test_can_send_a_message(self):
        message_type = MESSAGES.UPDATE_LEAD
        self.adapter.process(message_type)

        self.adapter.send_message.assert_called_once_with(message_type.value, recipient=message_type)

    def test_doesnt_send_a_message_if_not_configured(self):
        self.adapter.process('this_is_not_a_message_type')

        self.adapter.send_message.assert_not_called()

    def test_calls_method_if_avaliable(self):
        method_name = 'new_method'
        return_message = 'Returned message'
        setattr(self.adapter, method_name, lambda: return_message)
        self.adapter.messages[method_name] = method_name

        self.adapter.process(method_name)

        self.adapter.send_message.assert_called_once_with(return_message, recipient=method_name)

    def test_that_kwargs_passed_to_send_message(self):
        message_type = MESSAGES.UPDATE_LEAD
        kwargs = {'test': 'that', 'these': 'exist'}
        self.adapter.process(message_type, **kwargs)

        self.adapter.send_message.assert_called_once_with(message_type.value, recipient=message_type, **kwargs)

    def test_that_message_is_formatted(self):
        message_type = MESSAGES.UPDATE_LEAD
        self.adapter.messages[message_type] = '{message_to_format}'
        message = 'message value'

        self.adapter.process(message_type, message_to_format=message)

        self.adapter.send_message.assert_called_once_with(message, message_to_format=message, recipient=message_type)

    @override_settings(SEND_MESSAGES=False)
    def test_django_messages_used(self):
        request = make_request()

        self.adapter.process(MESSAGES.UPDATE_LEAD, request=request)

        messages = list(get_messages(request))
        self.assertEqual(len(messages), 1)
        self.assertTrue(MESSAGES.UPDATE_LEAD.value in messages[0].message)
        self.assertTrue(self.adapter.adapter_type in messages[0].message)


class TestMessageBackend(TestCase):
    def setUp(self):
        self.mocked_adapter = Mock(AdapterBase)
        self.backend = MessengerBackend

    def test_message_sent_to_adapter(self):
        adapter = self.mocked_adapter()
        messenger = self.backend(adapter)

        kwargs = {'request': None, 'user': None, 'submission': None}
        messenger(MESSAGES.UPDATE_LEAD, **kwargs)

        adapter.process.assert_called_once_with(MESSAGES.UPDATE_LEAD, **kwargs)

    def test_message_sent_to_all_adapter(self):
        adapters = [self.mocked_adapter(), self.mocked_adapter()]
        messenger = self.backend(*adapters)

        kwargs = {'request': None, 'user': None, 'submission': None}
        messenger(MESSAGES.UPDATE_LEAD, **kwargs)

        adapter = adapters[0]
        self.assertEqual(adapter.process.call_count, len(adapters))


@override_settings(SEND_MESSAGES=True)
class TestActivityAdapter(TestCase):
    def setUp(self):
        self.adapter = ActivityAdapter()

    def test_activity_created(self):
        message = 'test message'
        user = UserFactory()
        submission = ApplicationSubmissionFactory()

        self.adapter.send_message(message, user=user, submission=submission)

        self.assertEqual(Activity.objects.count(), 1)
        activity = Activity.objects.first()
        self.assertEqual(activity.user, user)
        self.assertEqual(activity.message, message)
        self.assertEqual(activity.submission, submission)

    def test_reviewers_message_no_removed(self):
        message = self.adapter.reviewers_updated([1], [])

        self.assertTrue('Added' in message)
        self.assertFalse('Removed' in message)
        self.assertTrue('1' in message)

    def test_reviewers_message_no_added(self):
        message = self.adapter.reviewers_updated([], [1])

        self.assertFalse('Added' in message)
        self.assertTrue('Removed' in message)
        self.assertTrue('1' in message)

    def test_reviewers_message_both(self):
        message = self.adapter.reviewers_updated([1], [2])

        self.assertTrue('Added' in message)
        self.assertTrue('Removed' in message)
        self.assertTrue('1' in message)
        self.assertTrue('2' in message)


class TestSlackAdapter(TestCase):
    target_url = 'https://my-slack-backend.com/incoming/my-very-secret-key'
    target_room = '<ROOM ID>'

    @override_settings(
        SLACK_DESTINATION_URL=target_url,
        SLACK_DESTINATION_ROOM=None,
    )
    @responses.activate
    def test_cant_send_with_no_room(self):
        adapter = SlackAdapter()
        adapter.send_message('my message', '')
        self.assertEqual(len(responses.calls), 0)

    @override_settings(
        SLACK_DESTINATION_URL=None,
        SLACK_DESTINATION_ROOM=target_room,
    )
    @responses.activate
    def test_cant_send_with_no_url(self):
        adapter = SlackAdapter()
        adapter.send_message('my message', '')
        self.assertEqual(len(responses.calls), 0)

    @override_settings(
        SLACK_DESTINATION_URL=target_url,
        SLACK_DESTINATION_ROOM=target_room,
    )
    @responses.activate
    def test_correct_payload(self):
        responses.add(responses.POST, self.target_url, status=200)
        adapter = SlackAdapter()
        message = 'my message'
        adapter.send_message(message, '')
        self.assertEqual(len(responses.calls), 1)
        self.assertDictEqual(
            json.loads(responses.calls[0].request.body),
            {
                'room': self.target_room,
                'message': message,
            }
        )

    @responses.activate
    def test_gets_lead_if_slack_set(self):
        adapter = SlackAdapter()
        submission = ApplicationSubmissionFactory()
        recipients = adapter.recipients(MESSAGES.COMMENT, submission)
        self.assertTrue(submission.lead.slack in recipients[0])

    @responses.activate
    def test_gets_black_if_slack_not_set(self):
        adapter = SlackAdapter()
        submission = ApplicationSubmissionFactory(lead__slack='')
        recipients = adapter.recipients(MESSAGES.COMMENT, submission)
        self.assertTrue(submission.lead.slack in recipients[0])


@override_settings(SEND_MESSAGES=True)
class TestEmailAdapter(TestCase):
    def test_email_new_submission(self):
        adapter = EmailAdapter()
        submission = ApplicationSubmissionFactory()
        adapter.process(MESSAGES.NEW_SUBMISSION, submission=submission)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [submission.user.email])

    def test_reviewers_email(self):
        adapter = EmailAdapter()
        reviewers = ReviewerFactory.create_batch(4)
        submission = ApplicationSubmissionFactory(status='external_review', reviewers=reviewers, workflow_stages=2)
        adapter.process(MESSAGES.READY_FOR_REVIEW, submission=submission)

        self.assertEqual(len(mail.outbox), 4)
        self.assertTrue(mail.outbox[0].subject, 'ready to review')
