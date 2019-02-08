import hashlib
import hmac
import json
from unittest.mock import Mock, patch

import responses

from django.core import mail
from django.test import TestCase, override_settings
from django.contrib.messages import get_messages

from opentech.apply.utils.testing import make_request
from opentech.apply.funds.tests.factories import ApplicationSubmissionFactory
from opentech.apply.review.tests.factories import ReviewFactory
from opentech.apply.users.tests.factories import ReviewerFactory, UserFactory

from opentech.apply.funds.models import AssignedReviewers
from ..models import Activity, Event, Message, INTERNAL, PUBLIC
from ..messaging import (
    AdapterBase,
    ActivityAdapter,
    EmailAdapter,
    MessengerBackend,
    neat_related,
    MESSAGES,
    SlackAdapter,
)
from .factories import CommentFactory, EventFactory, MessageFactory


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

    def log_message(self, message, recipient, event, status):
        pass


@override_settings(ROOT_URLCONF='opentech.apply.urls')
class AdapterMixin(TestCase):
    adapter = None

    def process_kwargs(self, message_type, **kwargs):
        if 'user' not in kwargs:
            kwargs['user'] = UserFactory()
        if 'submission' not in kwargs:
            kwargs['submission'] = ApplicationSubmissionFactory()
        if 'request' not in kwargs:
            kwargs['request'] = make_request()
        if message_type in neat_related:
            kwargs['related'] = kwargs.get('related', 'a thing')
        else:
            kwargs['related'] = None

        return kwargs

    def adapter_process(self, message_type, **kwargs):
        kwargs = self.process_kwargs(message_type, **kwargs)
        self.adapter.process(message_type, event=EventFactory(submission=kwargs['submission']), **kwargs)


@override_settings(SEND_MESSAGES=True)
class TestBaseAdapter(AdapterMixin, TestCase):
    def setUp(self):
        patched_class = patch.object(TestAdapter, 'send_message')
        self.mock_adapter = patched_class.start()
        self.adapter = TestAdapter()
        self.adapter.send_message.return_value = 'dummy_message'
        self.addCleanup(patched_class.stop)

    def test_can_send_a_message(self):
        message_type = MESSAGES.UPDATE_LEAD
        self.adapter_process(message_type)

        self.adapter.send_message.assert_called_once()
        self.assertEqual(self.adapter.send_message.call_args[0], (message_type.value,))

    def test_doesnt_send_a_message_if_not_configured(self):
        self.adapter_process('this_is_not_a_message_type')

        self.adapter.send_message.assert_not_called()

    def test_calls_method_if_avaliable(self):
        method_name = 'new_method'
        return_message = 'Returned message'
        setattr(self.adapter, method_name, lambda **kw: return_message)
        self.adapter.messages[method_name] = method_name

        self.adapter_process(method_name)

        self.adapter.send_message.assert_called_once()
        self.assertEqual(self.adapter.send_message.call_args[0], (return_message,))

    def test_that_kwargs_passed_to_send_message(self):
        message_type = MESSAGES.UPDATE_LEAD
        kwargs = {'test': 'that', 'these': 'exist'}
        self.adapter_process(message_type, **kwargs)

        self.adapter.send_message.assert_called_once()
        for key in kwargs:
            self.assertTrue(key in self.adapter.send_message.call_args[1])

    def test_that_message_is_formatted(self):
        message_type = MESSAGES.UPDATE_LEAD
        message = 'message value'

        with patch.dict(self.adapter.messages, {message_type: '{message_to_format}'}):
            self.adapter_process(message_type, message_to_format=message)

        self.adapter.send_message.assert_called_once()
        self.assertEqual(self.adapter.send_message.call_args[0], (message,))

    def test_can_include_extra_kwargs(self):
        message_type = MESSAGES.UPDATE_LEAD

        with patch.dict(self.adapter.messages, {message_type: '{extra}'}):
            with patch.object(self.adapter, 'extra_kwargs', return_value={'extra': 'extra'}):
                self.adapter_process(message_type)

        self.adapter.send_message.assert_called_once()
        self.assertTrue('extra' in self.adapter.send_message.call_args[1])

    @override_settings(SEND_MESSAGES=False)
    def test_django_messages_used(self):
        request = make_request()

        self.adapter_process(MESSAGES.UPDATE_LEAD, request=request)

        messages = list(get_messages(request))
        self.assertEqual(len(messages), 1)
        self.assertTrue(MESSAGES.UPDATE_LEAD.value in messages[0].message)
        self.assertTrue(self.adapter.adapter_type in messages[0].message)


class TestMessageBackend(TestCase):
    def setUp(self):
        self.mocked_adapter = Mock(AdapterBase)
        self.backend = MessengerBackend
        self.kwargs = {
            'related': None,
            'request': None,
            'user': UserFactory(),
            'submission': ApplicationSubmissionFactory(),
        }

    def test_message_sent_to_adapter(self):
        adapter = self.mocked_adapter()
        messenger = self.backend(adapter)

        messenger(MESSAGES.UPDATE_LEAD, **self.kwargs)

        adapter.process.assert_called_once_with(MESSAGES.UPDATE_LEAD, Event.objects.first(), **self.kwargs)

    def test_message_sent_to_all_adapter(self):
        adapters = [self.mocked_adapter(), self.mocked_adapter()]
        messenger = self.backend(*adapters)

        messenger(MESSAGES.UPDATE_LEAD, **self.kwargs)

        adapter = adapters[0]
        self.assertEqual(adapter.process.call_count, len(adapters))

    def test_event_created(self):
        adapters = [self.mocked_adapter(), self.mocked_adapter()]
        messenger = self.backend(*adapters)
        user = UserFactory()
        self.kwargs.update(user=user)

        messenger(MESSAGES.UPDATE_LEAD, **self.kwargs)

        self.assertEqual(Event.objects.count(), 1)
        self.assertEqual(Event.objects.first().type, MESSAGES.UPDATE_LEAD.name)
        self.assertEqual(Event.objects.first().get_type_display(), MESSAGES.UPDATE_LEAD.value)
        self.assertEqual(Event.objects.first().by, user)


@override_settings(SEND_MESSAGES=True)
class TestActivityAdapter(TestCase):
    def setUp(self):
        self.adapter = ActivityAdapter()

    def test_activity_created(self):
        message = 'test message'
        user = UserFactory()
        submission = ApplicationSubmissionFactory()

        self.adapter.send_message(message, user=user, submission=submission, submissions=[], related=None)

        self.assertEqual(Activity.objects.count(), 1)
        activity = Activity.objects.first()
        self.assertEqual(activity.user, user)
        self.assertEqual(activity.message, message)
        self.assertEqual(activity.submission, submission)

    def test_reviewers_message_no_removed(self):
        user = UserFactory()
        submission = ApplicationSubmissionFactory(reviewers=[user])
        assigned_reviewer = AssignedReviewers.objects.filter(submission=submission).first()

        message = self.adapter.reviewers_updated([assigned_reviewer], [])

        self.assertTrue('Added' in message)
        self.assertFalse('Removed' in message)
        self.assertTrue(str(user) in message)

    def test_reviewers_message_no_added(self):
        user = UserFactory()
        submission = ApplicationSubmissionFactory(reviewers=[user])
        assigned_reviewer = AssignedReviewers.objects.filter(submission=submission).first()
        message = self.adapter.reviewers_updated([], [assigned_reviewer])

        self.assertFalse('Added' in message)
        self.assertTrue('Removed' in message)
        self.assertTrue(str(user) in message)

    def test_reviewers_message_both(self):
        user_1 = UserFactory()
        user_2 = UserFactory()
        submission = ApplicationSubmissionFactory(reviewers=[user_1, user_2])
        assigned_reviewer_1 = AssignedReviewers.objects.filter(submission=submission, reviewer=user_1).first()
        assigned_reviewer_2 = AssignedReviewers.objects.filter(submission=submission, reviewer=user_2).first()
        message = self.adapter.reviewers_updated([assigned_reviewer_1], [assigned_reviewer_2])

        self.assertTrue('Added' in message)
        self.assertTrue('Removed' in message)
        self.assertTrue(str(user_1) in message)
        self.assertTrue(str(user_2) in message)

    def test_internal_transition_kwarg_for_invisible_transition(self):
        submission = ApplicationSubmissionFactory(status='post_review_discussion')
        kwargs = self.adapter.extra_kwargs(MESSAGES.TRANSITION, submission=submission)

        self.assertEqual(kwargs['visibility'], INTERNAL)

    def test_public_transition_kwargs(self):
        submission = ApplicationSubmissionFactory()
        kwargs = self.adapter.extra_kwargs(MESSAGES.TRANSITION, submission=submission)

        self.assertNotIn('visibility', kwargs)

    def test_handle_transition_public_to_public(self):
        submission = ApplicationSubmissionFactory(status='more_info')
        old_phase = submission.workflow.phases_for()[0]

        message = self.adapter.handle_transition(old_phase, submission)
        message = json.loads(message)

        self.assertIn(submission.phase.display_name, message[INTERNAL])
        self.assertIn(old_phase.display_name, message[INTERNAL])
        self.assertIn(submission.phase.public_name, message[PUBLIC])
        self.assertIn(old_phase.public_name, message[PUBLIC])

    def test_handle_transition_to_private_to_public(self):
        submission = ApplicationSubmissionFactory(status='more_info')
        old_phase = submission.workflow.phases_for()[1]

        message = self.adapter.handle_transition(old_phase, submission)
        message = json.loads(message)

        self.assertIn(submission.phase.display_name, message[INTERNAL])
        self.assertIn(old_phase.display_name, message[INTERNAL])
        self.assertIn(submission.phase.public_name, message[PUBLIC])
        self.assertIn(old_phase.public_name, message[PUBLIC])

    def test_handle_transition_to_public_to_private(self):
        submission = ApplicationSubmissionFactory(status='internal_review')
        old_phase = submission.workflow.phases_for()[0]

        message = self.adapter.handle_transition(old_phase, submission)

        self.assertIn(submission.phase.display_name, message)
        self.assertIn(old_phase.display_name, message)

    def test_lead_not_saved_on_activity(self):
        submission = ApplicationSubmissionFactory()
        user = UserFactory()
        self.adapter.send_message('a message', user=user, submission=submission, submissions=[], related=user)
        activity = Activity.objects.first()
        self.assertEqual(activity.related_object, None)

    def test_review_saved_on_activity(self):
        user = UserFactory()
        submission = ApplicationSubmissionFactory(reviewers=[user])
        review = ReviewFactory(submission=submission, author=user)
        self.adapter.send_message('a message', user=user, submission=submission, submissions=[], related=review)
        activity = Activity.objects.first()
        self.assertEqual(activity.related_object, review)


class TestSlackAdapter(AdapterMixin, TestCase):
    target_url = 'https://my-slack-backend.com/incoming/my-very-secret-key'
    target_room = '#<ROOM ID>'

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
        responses.add(responses.POST, self.target_url, status=200, body='OK')
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
    def test_gets_blank_if_slack_not_set(self):
        adapter = SlackAdapter()
        submission = ApplicationSubmissionFactory(lead__slack='')
        recipients = adapter.recipients(MESSAGES.COMMENT, submission)
        self.assertTrue(submission.lead.slack in recipients[0])

    @override_settings(
        SLACK_DESTINATION_URL=target_url,
        SLACK_DESTINATION_ROOM=target_room,
    )
    @responses.activate
    def test_message_with_good_response(self):
        responses.add(responses.POST, self.target_url, status=200, body='OK')

        self.adapter = SlackAdapter()
        self.adapter_process(MESSAGES.NEW_SUBMISSION)
        self.assertEqual(Message.objects.count(), 1)
        sent_message = Message.objects.first()
        self.assertEqual(sent_message.content[0:10], self.adapter.messages[MESSAGES.NEW_SUBMISSION][0:10])
        self.assertEqual(sent_message.status, '200: OK')

    @override_settings(
        SLACK_DESTINATION_URL=target_url,
        SLACK_DESTINATION_ROOM=target_room,
    )
    @responses.activate
    def test_message_with_bad_response(self):
        responses.add(responses.POST, self.target_url, status=400, body='Bad Request')

        self.adapter = SlackAdapter()
        self.adapter_process(MESSAGES.NEW_SUBMISSION)
        self.assertEqual(Message.objects.count(), 1)
        sent_message = Message.objects.first()
        self.assertEqual(sent_message.content[0:10], self.adapter.messages[MESSAGES.NEW_SUBMISSION][0:10])
        self.assertEqual(sent_message.status, '400: Bad Request')


@override_settings(SEND_MESSAGES=True)
class TestEmailAdapter(AdapterMixin, TestCase):
    adapter = EmailAdapter()

    def test_email_new_submission(self):
        submission = ApplicationSubmissionFactory()
        self.adapter_process(MESSAGES.NEW_SUBMISSION, submission=submission)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [submission.user.email])

    def test_no_email_private_comment(self):
        comment = CommentFactory(internal=True)

        self.adapter_process(MESSAGES.COMMENT, related=comment, submission=comment.submission)
        self.assertEqual(len(mail.outbox), 0)

    def test_no_email_own_comment(self):
        application = ApplicationSubmissionFactory()
        comment = CommentFactory(user=application.user, submission=application)

        self.adapter_process(MESSAGES.COMMENT, related=comment, user=comment.user, submission=comment.submission)
        self.assertEqual(len(mail.outbox), 0)

    def test_reviewers_email(self):
        reviewers = ReviewerFactory.create_batch(4)
        submission = ApplicationSubmissionFactory(status='external_review', reviewers=reviewers, workflow_stages=2)
        self.adapter_process(MESSAGES.READY_FOR_REVIEW, submission=submission)

        self.assertEqual(len(mail.outbox), 4)
        self.assertTrue(mail.outbox[0].subject, 'ready to review')

    def test_email_sent(self):
        self.adapter_process(MESSAGES.NEW_SUBMISSION)
        self.assertEqual(Message.objects.count(), 1)
        sent_message = Message.objects.first()
        self.assertEqual(sent_message.status, 'sent')

    def test_email_failed(self):
        with patch('django.core.mail.backends.locmem.EmailBackend.send_messages', side_effect=Exception('An error occurred')):
            self.adapter_process(MESSAGES.NEW_SUBMISSION)

        self.assertEqual(Message.objects.count(), 1)
        sent_message = Message.objects.first()
        self.assertEqual(sent_message.status, 'Error: An error occurred')


@override_settings(
    SEND_MESSAGES=True,
    EMAIL_BACKEND='anymail.backends.test.EmailBackend',
)
class TestAnyMailBehaviour(AdapterMixin, TestCase):
    adapter = EmailAdapter()
    TEST_API_KEY = 'TEST_API_KEY'

    # from: https://github.com/anymail/django-anymail/blob/7d8dbdace92d8addfcf0a517be0aaf481da11952/tests/test_mailgun_webhooks.py#L19
    def mailgun_sign(self, data, api_key=TEST_API_KEY):
        """Add a Mailgun webhook signature to data dict"""
        # Modifies the dict in place
        data.setdefault('timestamp', '1234567890')
        data.setdefault('token', '1234567890abcdef1234567890abcdef')
        data['signature'] = hmac.new(
            key=api_key.encode('ascii'),
            msg='{timestamp}{token}'.format(**data).encode('ascii'),
            digestmod=hashlib.sha256,
        ).hexdigest()

        return data

    def test_email_new_submission(self):
        submission = ApplicationSubmissionFactory()
        self.adapter_process(MESSAGES.NEW_SUBMISSION, submission=submission)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [submission.user.email])
        message = Message.objects.first()
        self.assertEqual(message.status, 'sent')
        # Anymail test Backend uses the index of the email as id: '0'
        self.assertEqual(message.external_id, '0')

    @override_settings(ANYMAIL_MAILGUN_API_KEY=TEST_API_KEY)
    def test_webhook_updates_status(self):
        message = MessageFactory()
        response = self.client.post(
            '/activity/anymail/mailgun/tracking/',
            data=self.mailgun_sign({
                'event': 'delivered',
                'Message-Id': message.external_id
            }),
            secure=True,
            json=True,
        )
        self.assertEqual(response.status_code, 200)
        message.refresh_from_db()
        self.assertTrue('delivered' in message.status)

    @override_settings(ANYMAIL_MAILGUN_API_KEY=TEST_API_KEY)
    def test_webhook_adds_reject_reason(self):
        message = MessageFactory()
        response = self.client.post(
            '/activity/anymail/mailgun/tracking/',
            data=self.mailgun_sign({
                'event': 'dropped',
                'reason': 'hardfail',
                'code': 607,
                'description': 'Marked as spam',
                'Message-Id': message.external_id
            }),
            secure=True,
            json=True,
        )
        self.assertEqual(response.status_code, 200)
        message.refresh_from_db()
        self.assertTrue('rejected' in message.status)
        self.assertTrue('spam' in message.status)
