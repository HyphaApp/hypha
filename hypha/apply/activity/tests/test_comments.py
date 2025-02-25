from django.test import TestCase
from django.urls import reverse_lazy

from hypha.apply.activity.tests.factories import CommentFactory


class TestCommentEdit(TestCase):
    def post_to_edit(self, comment_pk, message="my message"):
        return self.client.post(
            reverse_lazy("activity:edit-comment", kwargs={"pk": comment_pk}),
            secure=True,
            data={"message": message},
        )

    def test_cant_edit_if_not_author(self):
        comment = CommentFactory()
        response = self.post_to_edit(comment.pk)
        assert response.status_code == 302
        assert (
            reverse_lazy("users:passwordless_login_signup") + "?next=" in response.url
        )

    # def test_edit_updates_correctly(self):
    #     user = StaffFactory()
    #     comment = CommentFactory(user=user)
    #     self.client.force_login(user)

    #     new_message = "hi there"

    #     response = self.post_to_edit(comment.pk, new_message)

    #     self.assertEqual(response.status_code, 200, response.json())
    #     self.assertEqual(Activity.objects.count(), 2)

    #     comment.refresh_from_db()

    #     time = comment.timestamp.timestamp() * 1000

    #     self.assertEqual(time, response.json()["timestamp"])
    #     self.assertFalse(comment.current)
    #     self.assertEqual(response.json()["message"], new_message)

    # def test_incorrect_id_denied(self):
    #     response = self.post_to_edit(10000)
    #     self.assertEqual(response.status_code, 403, response.json())

    # def test_does_nothing_if_same_message_and_visibility(self):
    #     user = UserFactory()
    #     comment = CommentFactory(user=user)
    #     self.client.force_login(user)

    #     self.client.post(
    #         reverse_lazy("api:v1:comments-edit", kwargs={"pk": comment.pk}),
    #         secure=True,
    #         data={
    #             "message": comment.message,
    #             "visibility": comment.visibility,
    #         },
    #     )

    #     self.assertEqual(Activity.objects.count(), 1)

    # def test_staff_can_not_change_visibility(self):
    #     user = StaffFactory()
    #     comment = CommentFactory(user=user, visibility=APPLICANT)
    #     self.client.force_login(user)

    #     response = self.client.post(
    #         reverse_lazy("api:v1:comments-edit", kwargs={"pk": comment.pk}),
    #         secure=True,
    #         data={
    #             "message": "the new message",
    #             "visibility": ALL,
    #         },
    #     )

    #     self.assertEqual(response.status_code, 200, response.json())
    #     self.assertEqual(response.json()["visibility"], APPLICANT)

    # def test_out_of_order_does_nothing(self):
    #     user = ApplicantFactory()  # any role assigned user
    #     comment = CommentFactory(user=user)
    #     self.client.force_login(user)

    #     new_message = "hi there"
    #     newer_message = "hello there"

    #     response_one = self.post_to_edit(comment.pk, new_message)
    #     response_two = self.post_to_edit(comment.pk, newer_message)

    #     self.assertEqual(response_one.status_code, 200, response_one.json())
    #     self.assertEqual(response_two.status_code, 404, response_two.json())
    #     self.assertEqual(Activity.objects.count(), 2)
