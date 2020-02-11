from unittest import TestCase

from opentech.apply.review.models import ReviewForm
from .factories import ReviewFormFactory


class TestReviewFormAdminForm(TestCase):

    def test_can_create_review_form(self):
        review_form = ReviewFormFactory()
        self.assertEqual(ReviewForm.objects.last(), review_form)
