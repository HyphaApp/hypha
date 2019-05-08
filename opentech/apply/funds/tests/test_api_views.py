from django.test import TestCase, override_settings
from django.urls import reverse_lazy
from django.utils import timezone

from opentech.apply.activity.models import Activity, PUBLIC, PRIVATE
from opentech.apply.activity.tests.factories import CommentFactory

from opentech.apply.users.tests.factories import UserFactory


@override_settings(ROOT_URLCONF='opentech.apply.urls')
class TestCommentEdit(TestCase):
    def post_to_edit(self, comment_pk, message='my message'):
        return self.client.post(
            reverse_lazy('funds:api:comments:edit', kwargs={'pk': comment_pk}),
            secure=True,
            data={'message': message},
        )

    def test_cant_edit_if_not_author(self):
        comment = CommentFactory()
        response = self.post_to_edit(comment.pk)
        self.assertEqual(response.status_code, 403)

    def test_edit_updates_correctly(self):
        user = UserFactory()
        comment = CommentFactory(user=user)
        self.client.force_login(user)

        new_message = 'hi there'

        response = self.post_to_edit(comment.pk, new_message)

        self.assertEqual(response.status_code, 200, response.json())
        self.assertEqual(Activity.objects.count(), 2)

        comment.refresh_from_db()

        # Match the behaviour of DRF
        time = comment.timestamp.astimezone(timezone.get_current_timezone()).isoformat()
        if time.endswith('+00:00'):
            time = time[:-6] + 'Z'

        self.assertEqual(time, response.json()['timestamp'])
        self.assertFalse(comment.current)
        self.assertEqual(response.json()['message'], new_message)

    def test_incorrect_id_denied(self):
        response = self.post_to_edit(10000)
        self.assertEqual(response.status_code, 403, response.json())

    def test_does_nothing_if_same_message(self):
        user = UserFactory()
        comment = CommentFactory(user=user)
        self.client.force_login(user)

        self.post_to_edit(comment.pk, comment.message)
        self.assertEqual(Activity.objects.count(), 1)

    def test_cant_change_visibility(self):
        user = UserFactory()
        comment = CommentFactory(user=user, visibility=PRIVATE)
        self.client.force_login(user)

        response = self.client.post(
            reverse_lazy('funds:api:comments:edit', kwargs={'pk': comment.pk}),
            secure=True,
            data={
                'message': 'the new message',
                'visibility': PUBLIC,
            },
        )

        self.assertEqual(response.status_code, 200, response.json())
        self.assertEqual(response.json()['visibility'], PRIVATE)

    def test_out_of_order_does_nothing(self):
        user = UserFactory()
        comment = CommentFactory(user=user)
        self.client.force_login(user)

        new_message = 'hi there'
        newer_message = 'hello there'

        response_one = self.post_to_edit(comment.pk, new_message)
        response_two = self.post_to_edit(comment.pk, newer_message)

        self.assertEqual(response_one.status_code, 200, response_one.json())
        self.assertEqual(response_two.status_code, 404, response_two.json())
        self.assertEqual(Activity.objects.count(), 2)
