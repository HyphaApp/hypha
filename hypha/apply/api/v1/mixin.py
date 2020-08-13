from django.shortcuts import get_object_or_404

from hypha.apply.funds.models import ApplicationSubmission
from hypha.apply.review.models import Review


class SubmissionNestedMixin:
    def get_submission_object(self):
        return get_object_or_404(
            ApplicationSubmission, id=self.kwargs['submission_pk']
        )


class ReviewNestedMixin:
    def get_review_object(self):
        return get_object_or_404(
            Review, id=self.kwargs['review_pk']
        )
