from django.shortcuts import get_object_or_404
from django.views.generic import CreateView

from opentech.apply.funds.models import ApplicationSubmission
from .forms import ConceptReviewForm, ProposalReviewForm
from .models import Review


class ReviewCreateView(CreateView):
    model = Review

    def get_context_data(self, **kwargs):
        self.submission = get_object_or_404(ApplicationSubmission, id=self.kwargs['submission_pk'])
        has_submitted_review = Review.objects.filter(submission=self.submission, author=self.request.user).exists()

        return super().get_context_data(
            submission=self.submission,
            has_submitted_review=has_submitted_review,
            **kwargs
        )

    def get_form_class(self):
        forms = [ConceptReviewForm, ProposalReviewForm]
        index = [
            i for i, stage in enumerate(self.submission.workflow.stages)
            if self.submission.stage.name == stage.name
        ][0]
        return forms[index]

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['submission'] = self.submission
        return kwargs

    def get_success_url(self):
        return self.submission.get_absolute_url()
