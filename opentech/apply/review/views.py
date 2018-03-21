from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, ListView

from opentech.apply.funds.models import ApplicationSubmission
from opentech.apply.users.decorators import staff_required

from .forms import ConceptReviewForm, ProposalReviewForm
from .models import Review


class ReviewContextMixin:
    def get_context_data(self, **kwargs):
        staff_reviews = self.object.reviews.by_staff()
        reviewer_reviews = self.object.reviews.by_reviewers().exclude(id__in=staff_reviews)
        return super().get_context_data(
            staff_reviews=staff_reviews,
            reviewer_reviews=reviewer_reviews,
            **kwargs,
        )


def get_form_for_stage(submission):
    forms = [ConceptReviewForm, ProposalReviewForm]
    index = [
        i for i, stage in enumerate(submission.workflow.stages)
        if submission.stage.name == stage.name
    ][0]
    return forms[index]


class ReviewCreateView(CreateView):
    model = Review

    def dispatch(self, request, *args, **kwargs):
        self.submission = get_object_or_404(ApplicationSubmission, id=self.kwargs['submission_pk'])

        if not self.submission.phase.has_perm('review', request.user) or not self.submission.has_permission_to_review(request.user):
            raise PermissionDenied()

        if self.request.POST and self.submission.reviewed_by(request.user):
            return self.get(request, *args, **kwargs)

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        has_submitted_review = self.submission.reviewed_by(request.user)
        return super().get_context_data(
            submission=self.submission,
            has_submitted_review=has_submitted_review,
            **kwargs
        )

    def get_form_class(self):
        return get_form_for_stage(self.submission)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['submission'] = self.submission
        return kwargs

    def get_success_url(self):
        return self.submission.get_absolute_url()


@method_decorator(staff_required, name='dispatch')
class ReviewListView(ListView):
    model = Review

    def get_queryset(self):
        self.submission = get_object_or_404(ApplicationSubmission, id=self.kwargs['submission_pk'])
        self.queryset = self.model.objects.filter(submission=self.submission)
        return super().get_queryset()

    def get_context_data(self, **kwargs):
        form_used = get_form_for_stage(self.submission)
        review_data = {}

        for review in self.object_list:
            # Add the name header row
            review_data.setdefault('', []).append(str(review.author))

        for name, field in form_used.base_fields.items():
            try:
                # Add titles which exist
                title = form_used.titles[field.group]
                review_data.setdefault(title, [])
            except AttributeError:
                pass

            for review in self.object_list:
                value = review.review[name]
                try:
                    choices = dict(field.choices)
                except AttributeError:
                    pass
                else:
                    # Update the stored value to the display value
                    value = choices[int(value)]

                review_data.setdefault(field.label, []).append(str(value))

        return super().get_context_data(
            submission=self.submission,
            review_data=review_data,
            **kwargs
        )
