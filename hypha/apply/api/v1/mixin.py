from django.shortcuts import get_object_or_404

from hypha.apply.funds.models import ApplicationSubmission


class SubmissionNestedMixin:
    def get_submission_object(self):
        return get_object_or_404(
            ApplicationSubmission, id=self.kwargs['submission_pk']
        )
