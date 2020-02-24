from django.test import TestCase

from ..models import Activity
from .factories import CommentFactory


class TestActivityOnlyIncludesCurrent(TestCase):
    def test_doesnt_include_non_current(self):
        CommentFactory()
        CommentFactory(current=False)
        self.assertEqual(Activity.comments.count(), 1)
