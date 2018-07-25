from unittest.mock import patch

from django.test import TestCase

from ..messaging import AdapterBase, MESSAGES


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
