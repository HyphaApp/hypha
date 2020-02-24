from django.test import TestCase

from .factories import CommentFactory
from ..models import Activity


class TestActivityOnlyIncludesCurrent(TestCase):
    def test_doesnt_include_non_current(self):
        CommentFactory()
        CommentFactory(current=False)
        self.assertEqual(Activity.comments.count(), 1)
