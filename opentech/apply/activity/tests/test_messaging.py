from unittest.mock import Mock, patch

from django.test import TestCase
from django.contrib.messages import get_messages

from opentech.apply.utils.tests import make_request
from opentech.apply.funds.tests.factories import ApplicationSubmissionFactory
from opentech.apply.users.tests.factories import UserFactory

from ..models import Activity
from ..messaging import (
    AdapterBase,
    ActivityAdapter,
    MessageAdapter,
    MessengerBackend,
    MESSAGES,
)


class TestAdapter(AdapterBase):
    """A test class which will pass the message type to send_message"""
    messages = {
        enum: enum.value
        for enum in MESSAGES.__members__.values()
    }

    def send_message(self, message, **kwargs):
        pass


class TestBaseAdapter(TestCase):
    def setUp(self):
        patched_class = patch.object(TestAdapter, 'send_message')
        self.mock_adapter = patched_class.start()
        self.adapter = TestAdapter()
        self.addCleanup(patched_class.stop)

    def test_can_send_a_message(self):
        message_type = MESSAGES.UPDATE_LEAD
        self.adapter.process(message_type)

        self.adapter.send_message.assert_called_once_with(message_type.value)

    def test_doesnt_send_a_message_if_not_configured(self):
        self.adapter.process('this_is_not_a_message_type')

        self.adapter.send_message.assert_not_called()

    def test_calls_method_if_avaliable(self):
        method_name = 'new_method'
        return_message = 'Returned message'
        setattr(self.adapter, method_name, lambda: return_message)
        self.adapter.messages[method_name] = method_name

        self.adapter.process(method_name)

        self.adapter.send_message.assert_called_once_with(return_message)

    def test_that_kwargs_passed_to_send_message(self):
        message_type = MESSAGES.UPDATE_LEAD
        kwargs = {'test': 'that', 'these': 'exist'}
        self.adapter.process(message_type, **kwargs)

        self.adapter.send_message.assert_called_once_with(message_type.value, **kwargs)

    def test_that_message_is_formatted(self):
        message_type = MESSAGES.UPDATE_LEAD
        self.adapter.messages[message_type] = '{message}'
        message = 'message value'

        self.adapter.process(message_type, message=message)

        self.adapter.send_message.assert_called_once_with(message, message=message)


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


class TestDjangoMessagesAdapter(TestCase):
    def test_message_added(self):
        adapter = MessageAdapter()
        request = make_request()

        message = 'test message'
        adapter.send_message(message, request=request)

        messages = list(get_messages(request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].message, message)


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
