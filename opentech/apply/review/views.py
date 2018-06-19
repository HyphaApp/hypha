from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView
from django.views.generic.detail import SingleObjectTemplateResponseMixin
from django.views.generic.edit import ProcessFormView, ModelFormMixin

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
    index = submission.workflow.stages.index(submission.stage)
    return forms[index]


class CreateOrUpdateView(SingleObjectTemplateResponseMixin, ModelFormMixin, ProcessFormView):

    def get(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
        except self.model.DoesNotExist:
            self.object = None

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
        except self.model.DoesNotExist:
            self.object = None

        return super().post(request, *args, **kwargs)


class ReviewCreateOrUpdateView(CreateOrUpdateView):
    model = Review
    template_name = 'review/review_form.html'

    def get_object(self, queryset=None):
        return self.model.objects.get(submission=self.submission, author=self.request.user)

    def dispatch(self, request, *args, **kwargs):
        self.submission = get_object_or_404(ApplicationSubmission, id=self.kwargs['submission_pk'])

        if not self.submission.phase.permissions.can_review(request.user) or not self.submission.has_permission_to_review(request.user):
            raise PermissionDenied()

        if self.request.POST and self.submission.reviewed_by(request.user):
            return self.get(request, *args, **kwargs)

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        has_submitted_review = self.submission.reviewed_by(self.request.user)
        return super().get_context_data(
            submission=self.submission,
            has_submitted_review=has_submitted_review,
            title="Update Review draft" if self.object else 'Create Review',
            **kwargs
        )

    def get_form_class(self):
        return get_form_for_stage(self.submission)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['submission'] = self.submission

        if self.object:
            kwargs['initial'] = self.object.review
            kwargs['initial']['recommendation'] = self.object.recommendation

        return kwargs

    def get_success_url(self):
        return self.submission.get_absolute_url()


class ReviewDetailView(DetailView):
    model = Review

    def dispatch(self, request, *args, **kwargs):
        review = self.get_object()
        author = review.author

        if request.user != author and not request.user.is_superuser and request.user != review.submission.lead:
            raise PermissionDenied

        if review.is_draft:
            return HttpResponseRedirect(reverse_lazy('apply:reviews:form', args=(review.submission.id,)))

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        review = self.get_object().review
        form_used = get_form_for_stage(self.get_object().submission)
        review_data = {}

        for name, field in form_used.base_fields.items():
            try:
                # Add titles which exist
                title = form_used.titles[field.group]
                # Setting the value to a flag, so the output is treated slightly differently
                # This will change with the StreamForms implementation
                review_data.setdefault(title, '<field_group_title>')
            except AttributeError:
                pass

            value = review[name]
            try:
                choices = dict(field.choices)
            except AttributeError:
                pass
            else:
                # Update the stored value to the display value
                value = choices[int(value)]

            review_data.setdefault(field.label, str(value))
        return super().get_context_data(
            review_data=review_data,
            **kwargs
        )


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
            review_data.setdefault('Score', []).append(str(review.score))

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
