from unittest.mock import Mock, patch

from django.test import TestCase

from ..messaging import AdapterBase, MessengerBackend, MESSAGES


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
