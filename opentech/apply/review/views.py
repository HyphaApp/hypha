from collections import defaultdict

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.loader import get_template
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, ListView, DetailView

from wagtail.core.blocks import RichTextBlock

from opentech.apply.activity.messaging import messenger, MESSAGES
from opentech.apply.funds.models import ApplicationSubmission
from opentech.apply.review.blocks import RecommendationBlock, RecommendationCommentsBlock
from opentech.apply.review.forms import ReviewModelForm, ReviewOpinionForm
from opentech.apply.stream_forms.models import BaseStreamForm
from opentech.apply.users.decorators import staff_required
from opentech.apply.users.models import User
from opentech.apply.utils.views import CreateOrUpdateView

from .models import Review


class ReviewContextMixin:
    def get_context_data(self, **kwargs):
        assigned = self.object.assigned.order_by('role__order').select_related('reviewer')
        reviews = self.object.reviews.submitted().select_related('author')

        reviews_dict = {}
        for review in reviews:
            reviews_dict[review.author.pk] = review

        # Get all the authors of opinions, these authors should not show up in the 'xxx_not_reviewed' lists
        opinion_authors = User.objects.filter(pk__in=self.object.reviews.opinions().values('author')).distinct()

        reviews_block = defaultdict(list)
        for assigned_reviewer in assigned:
            reviewer = assigned_reviewer.reviewer
            role = assigned_reviewer.role
            review = reviews_dict.get(reviewer.pk, None)
            key = None
            if role:
                if review:
                    key = 'role_reviewed'
                elif reviewer not in opinion_authors:
                    key = 'role_not_reviewed'
            elif reviewer.is_apply_staff:
                if review:
                    key = 'staff_reviewed'
                elif review not in opinion_authors:
                    key = 'staff_not_reviewed'
            else:
                if review:
                    key = 'external_reviewed'
                else:
                    key = 'external_not_reviewed'
            if key:  # Do not add this reviewer to any list if they haven't reviewed but have left an opinion
                review_info_dict = {
                    'reviewer': reviewer,
                    'review': review,
                    'role': role,
                }
                opinions_list = []
                if review:
                    # Loop through all opinions and include the current author's role for this submission
                    for opinion in review.opinions.all():
                        opinions_list.append({
                            'author': opinion.author,
                            'opinion': opinion.get_opinion_display(),
                            'role': opinion.get_author_role(),
                        })
                    review_info_dict['opinions'] = opinions_list
                reviews_block[key].append(review_info_dict)

        # Calculate the recommendation based on role and staff reviews
        recommendation = self.object.reviews.by_staff().recommendation()

        return super().get_context_data(
            reviews_block=reviews_block,
            recommendation=recommendation,
            reviews_exist=reviews.count(),
            assigned_staff=assigned.staff().exists(),
            **kwargs,
        )


def get_fields_for_stage(submission):
    forms = submission.get_from_parent('review_forms').all()
    index = submission.workflow.stages.index(submission.stage)
    try:
        return forms[index].form.form_fields
    except IndexError:
        return forms[0].form.form_fields


@method_decorator(login_required, name='dispatch')
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
                related=self.object,
            )
        return response

    def get_success_url(self):
        return self.submission.get_absolute_url()


class ReviewDisplay(DetailView):
    model = Review

    def get_context_data(self, **kwargs):
        review = self.get_object()
        if review.author != self.request.user:
            consensus_form = ReviewOpinionForm(
                instance=review.opinions.filter(author=self.request.user).first(),
            )
        else:
            consensus_form = None
        return super().get_context_data(
            form=consensus_form,
            **kwargs,
        )

    def dispatch(self, request, *args, **kwargs):
        review = self.get_object()
        author = review.author

        if request.user != author and not request.user.is_superuser and not request.user.is_apply_staff:
            raise PermissionDenied

        if review.is_draft:
            return HttpResponseRedirect(reverse_lazy('apply:submissions:reviews:form', args=(review.submission.id,)))

        return super().dispatch(request, *args, **kwargs)


class ReviewOpinionFormView(CreateView):
    template_name = 'review/review_detail.html'
    form_class = ReviewOpinionForm
    model = Review

    def get_form_kwargs(self):
        self.object = self.get_object()
        kwargs = super().get_form_kwargs()
        instance = kwargs['instance']
        kwargs['instance'] = instance.opinions.filter(author=self.request.user).first()
        return kwargs

    def form_valid(self, form):
        self.review = self.get_object()
        form.instance.author = self.request.user
        form.instance.review = self.review
        response = super().form_valid(form)

        messenger(
            MESSAGES.REVIEW_OPINION,
            request=self.request,
            user=self.request.user,
            submission=self.review.submission,
            related=form.instance,
        )
        return response

    def get_success_url(self):
        return self.review.get_absolute_url()


@method_decorator(login_required, name='dispatch')
class ReviewDetailView(DetailView):
    def get(self, request, *args, **kwargs):
        view = ReviewDisplay.as_view()
        return view(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        view = ReviewOpinionFormView.as_view()
        return view(request, *args, **kwargs)


@method_decorator(staff_required, name='dispatch')
class ReviewListView(ListView):
    model = Review

    def get_queryset(self):
        self.submission = get_object_or_404(ApplicationSubmission, id=self.kwargs['submission_pk'])
        self.queryset = self.model.objects.filter(submission=self.submission, is_draft=False)
        return super().get_queryset()

    def should_display(self, field):
        return not isinstance(field.block, (RecommendationBlock, RecommendationCommentsBlock, RichTextBlock))

    def get_context_data(self, **kwargs):
        review_data = {}

        # Add the header rows
        review_data['title'] = {'question': '', 'answers': list()}
        review_data['opinions'] = {'question': 'Opinions', 'answers': list()}
        review_data['score'] = {'question': 'Overall Score', 'answers': list()}
        review_data['recommendation'] = {'question': 'Recommendation', 'answers': list()}
        review_data['revision'] = {'question': 'Revision', 'answers': list()}
        review_data['comments'] = {'question': 'Comments', 'answers': list()}

        responses = self.object_list.count()

        for i, review in enumerate(self.object_list):
            review_data['title']['answers'].append('<a href="{}">{}</a>'.format(review.get_absolute_url(), review.author))
            if review.opinions:
                opinions_template = get_template('review/includes/review_opinions_list.html')
                opinions_html = opinions_template.render({'opinions': review.opinions.all()})
                review_data['opinions']['answers'].append(opinions_html)
            else:
                review_data['opinions']['answers'].append("")
            review_data['score']['answers'].append(str(review.get_score_display()))
            review_data['recommendation']['answers'].append(review.get_recommendation_display())
            review_data['comments']['answers'].append(review.get_comments_display(include_question=False))
            if review.for_latest:
                revision = 'Current'
            else:
                revision = '<a href="{}">Compare</a>'.format(review.get_compare_url())
            review_data['revision']['answers'].append(revision)

            for field_id in review.fields:
                field = review.field(field_id)
                data = review.data(field_id)
                if self.should_display(field):
                    question = field.value['field_label']
                    review_data.setdefault(field.id, {'question': question, 'answers': [''] * responses})
                    review_data[field.id]['answers'][i] = field.block.render(None, {'data': data})

        return super().get_context_data(
            submission=self.submission,
            review_data=review_data,
            **kwargs
        )
