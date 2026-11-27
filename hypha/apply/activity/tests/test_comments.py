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
