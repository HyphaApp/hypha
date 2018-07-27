import json

from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView

from opentech.apply.activity.messaging import messenger, MESSAGES
from opentech.apply.funds.models import ApplicationSubmission
from opentech.apply.review.blocks import ScoreFieldBlock, RecommendationBlock
from opentech.apply.review.forms import ReviewModelForm
from opentech.apply.review.options import RATE_CHOICE_NA, RATE_CHOICES_DICT
from opentech.apply.stream_forms.models import BaseStreamForm
from opentech.apply.users.decorators import staff_required
from opentech.apply.utils.views import CreateOrUpdateView

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


def get_fields_for_stage(submission):
    forms = submission.page.specific.review_forms.all()
    index = submission.workflow.stages.index(submission.stage)
    try:
        return forms[index].form.form_fields
    except IndexError:
        return forms[0].form.form_fields


class ReviewCreateOrUpdateView(BaseStreamForm, CreateOrUpdateView):
    submission_form_class = ReviewModelForm
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

    def get_defined_fields(self):
        return get_fields_for_stage(self.submission)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['submission'] = self.submission

        if self.object:
            kwargs['initial'] = self.object.form_data

        return kwargs

    def form_valid(self, form):
        form.instance.form_fields = self.get_defined_fields()
        response = super().form_valid(form)

        if not self.object.is_draft:
            messenger(
                MESSAGES.NEW_REVIEW,
                request=self.request,
                user=self.object.author,
                submission=self.submission,
                review=self.object,
            )
        return response

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


@method_decorator(staff_required, name='dispatch')
class ReviewListView(ListView):
    model = Review

    def get_queryset(self):
        self.submission = get_object_or_404(ApplicationSubmission, id=self.kwargs['submission_pk'])
        self.queryset = self.model.objects.filter(submission=self.submission)
        return super().get_queryset()

    def get_context_data(self, **kwargs):
        review_data = {}

        # Add the header rows
        review_data['title'] = {'question': '', 'answers': list()}
        review_data['score'] = {'question': 'Overall Score', 'answers': list()}
        review_data['recommendation'] = {'question': 'Recommendation', 'answers': list()}

        for review in self.object_list:
            review_data['title']['answers'].append(str(review.author))
            review_data['score']['answers'].append(str(review.score))
            review_data['recommendation']['answers'].append(review.get_recommendation_display())

            for data, field in review.data_and_fields():
                if not isinstance(field.block, RecommendationBlock):
                    question = field.value['field_label']
                    review_data.setdefault(field.id, {'question': question, 'answers': list()})

                    if isinstance(field.block, ScoreFieldBlock):
                        value = json.loads(data)
                        rating_value = int(value[1])
                        rating = RATE_CHOICES_DICT.get(rating_value, RATE_CHOICE_NA)
                        comment = str(value[0])
                        review_data[field.id]['answers'].append(rating + comment)
                    else:
                        review_data[field.id]['answers'].append(str(data))

        return super().get_context_data(
            submission=self.submission,
            review_data=review_data,
            **kwargs
        )
