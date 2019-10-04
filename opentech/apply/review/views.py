from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.loader import get_template
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, ListView, DetailView, DeleteView, UpdateView

from wagtail.core.blocks import RichTextBlock

from opentech.apply.activity.messaging import messenger, MESSAGES
from opentech.apply.funds.models import ApplicationSubmission, AssignedReviewers
from opentech.apply.funds.workflow import INITIAL_STATE
from opentech.apply.review.blocks import RecommendationBlock, RecommendationCommentsBlock
from opentech.apply.review.forms import ReviewModelForm, ReviewOpinionForm
from opentech.apply.stream_forms.models import BaseStreamForm
from opentech.apply.users.decorators import staff_required
from opentech.apply.users.groups import REVIEWER_GROUP_NAME
from opentech.apply.utils.views import CreateOrUpdateView
from opentech.apply.utils.image import generate_image_tag

from .models import Review
from .options import DISAGREE


class ReviewContextMixin:
    def get_context_data(self, **kwargs):
        assigned_reviewers = self.object.assigned.review_order()

        if not self.object.stage.has_external_review:
            assigned_reviewers = assigned_reviewers.staff()

        # Calculate the recommendation based on role and staff reviews
        recommendation = self.object.reviews.by_staff().recommendation()

        return super().get_context_data(
            hidden_types=[REVIEWER_GROUP_NAME],
            staff_reviewers_exist=assigned_reviewers.staff().exists(),
            assigned_reviewers=assigned_reviewers,
            recommendation=recommendation,
            **kwargs,
        )


def get_fields_for_stage(submission):
    forms = submission.get_from_parent('review_forms').all()
    index = submission.workflow.stages.index(submission.stage)
    try:
        return forms[index].form.form_fields
    except IndexError:
        return forms[0].form.form_fields


class ReviewEditView(UserPassesTestMixin, BaseStreamForm, UpdateView):
    submission_form_class = ReviewModelForm
    model = Review
    template_name = 'review/review_edit_form.html'
    raise_exception = True

    def test_func(self):
        review = self.get_object()
        return self.request.user.has_perm('review.change_review') or self.request.user == review.author.reviewer

    def get_context_data(self, **kwargs):
        review = self.get_object()
        return super().get_context_data(
            submission=review.submission,
            title="Edit Review",
            **kwargs
        )

    def get_defined_fields(self):
        review = self.get_object()
        return get_fields_for_stage(review.submission)

    def get_form_kwargs(self):
        review = self.get_object()
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['submission'] = review.submission

        if self.object:
            kwargs['initial'] = self.object.form_data

        return kwargs

    def form_valid(self, form):
        review = self.get_object()
        messenger(
            MESSAGES.EDIT_REVIEW,
            user=self.request.user,
            request=self.request,
            source=review.submission,
            related=review,
        )
        response = super().form_valid(form)
        return response

    def get_success_url(self):
        review = self.get_object()
        return reverse_lazy('funds:submissions:detail', args=(review.submission.id,))


@method_decorator(login_required, name='dispatch')
class ReviewCreateOrUpdateView(BaseStreamForm, CreateOrUpdateView):
    submission_form_class = ReviewModelForm
    model = Review
    template_name = 'review/review_form.html'

    def get_object(self, queryset=None):
        return self.model.objects.get(submission=self.submission, author__reviewer=self.request.user)

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
        form.instance.author, _ = AssignedReviewers.objects.get_or_create_for_user(
            submission=self.submission,
            reviewer=self.request.user,
        )

        response = super().form_valid(form)

        if not self.object.is_draft:
            messenger(
                MESSAGES.NEW_REVIEW,
                request=self.request,
                user=self.request.user,
                source=self.submission,
                related=self.object,
            )

            # Automatic workflow actions.
            submission_stepped_phases = self.submission.workflow.stepped_phases
            action = None
            if self.submission.status == INITIAL_STATE:
                # Automatically transition the application to "Internal review".
                action = submission_stepped_phases[1][0].name
            elif self.submission.status == submission_stepped_phases[1][0].name and self.submission.reviews.count() > 1:
                # Automatically transition the application to "Ready for discussion".
                action = submission_stepped_phases[2][0].name
            elif self.submission.status == 'proposal_discussion':
                # Automatically transition the proposal to "Internal review".
                action = 'proposal_internal_review'
            elif self.submission.status == 'external_review' and self.submission.reviews.by_reviewers().count() > 1:
                # Automatically transition the proposal to "Ready for discussion".
                action = 'post_external_review_discussion'

            # If action is set run perform_transition().
            if action:
                try:
                    self.submission.perform_transition(
                        action,
                        self.request.user,
                        request=self.request,
                        notify=False,
                    )
                except (PermissionDenied, KeyError):
                    pass

        return response

    def get_success_url(self):
        return self.submission.get_absolute_url()


class ReviewDisplay(UserPassesTestMixin, DetailView):
    model = Review
    raise_exception = True

    def get_context_data(self, **kwargs):
        review = self.get_object()
        if review.author.reviewer != self.request.user:
            consensus_form = ReviewOpinionForm(
                instance=review.opinions.filter(author__reviewer=self.request.user).first(),
            )
        else:
            consensus_form = None
        return super().get_context_data(
            form=consensus_form,
            **kwargs,
        )

    def test_func(self):
        review = self.get_object()
        user = self.request.user
        author = review.author.reviewer
        submission = review.submission
        partner_has_access = submission.partners.filter(pk=user.pk).exists()

        if user.is_apply_staff:
            return True

        if user == author:
            return True

        if user.is_reviewer and review.reviewer_visibility:
            return True

        if user.is_partner and partner_has_access and review.reviewer_visibility and submission.user != user:
            return True

        if user.is_community_reviewer and submission.community_review and review.reviewer_visibility and submission.user != user:
            return True

        return False

    def dispatch(self, request, *args, **kwargs):
        review = self.get_object()

        if review.is_draft:
            return HttpResponseRedirect(reverse_lazy('apply:submissions:reviews:form', args=(review.submission.id,)))

        return super().dispatch(request, *args, **kwargs)


class ReviewOpinionFormView(UserPassesTestMixin, CreateView):
    template_name = 'review/review_detail.html'
    form_class = ReviewOpinionForm
    model = Review
    raise_exception = True

    def get_form_kwargs(self):
        self.object = self.get_object()
        kwargs = super().get_form_kwargs()
        instance = kwargs['instance']
        kwargs['instance'] = instance.opinions.filter(author__reviewer=self.request.user).first()
        return kwargs

    def test_func(self):
        review = self.get_object()
        user = self.request.user
        author = review.author.reviewer
        submission = review.submission
        partner_has_access = submission.partners.filter(pk=user.pk).exists()

        if user.is_apply_staff:
            return True

        if user == author:
            return False

        if user.is_reviewer and review.reviewer_visibility:
            return True

        if user.is_partner and partner_has_access and review.reviewer_visibility and submission.user != user:
            return True

        if user.is_community_reviewer and submission.community_review and review.reviewer_visibility and submission.user != user:
            return True

        return False

    def form_valid(self, form):
        self.review = self.get_object()
        author, _ = AssignedReviewers.objects.get_or_create_for_user(
            submission=self.review.submission,
            reviewer=self.request.user,
        )
        form.instance.author = author
        form.instance.review = self.review
        response = super().form_valid(form)
        opinion = form.instance

        messenger(
            MESSAGES.REVIEW_OPINION,
            request=self.request,
            user=self.request.user,
            source=self.review.submission,
            related=opinion,
        )

        if opinion.opinion == DISAGREE:
            return HttpResponseRedirect(reverse_lazy('apply:submissions:reviews:form', args=(self.review.submission.pk,)))
        else:
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
        ordered_reviewers = AssignedReviewers.objects.filter(submission=self.submission).reviewed().review_order()

        reviews = {review.author: review for review in self.object_list}
        for i, reviewer in enumerate(ordered_reviewers):
            review = reviews[reviewer]
            author = '<a href="{}"><span>{}</span></a>'.format(review.get_absolute_url(), review.author)
            if review.author.role:
                author += generate_image_tag(review.author.role.icon, '12x12')
            author = f'<div>{author}</div>'

            review_data['title']['answers'].append(author)
            opinions_template = get_template('review/includes/review_opinions_list.html')
            opinions_html = opinions_template.render({'opinions': review.opinions.select_related('author').all()})
            review_data['opinions']['answers'].append(opinions_html)
            review_data['score']['answers'].append(review.get_score_display)
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


class ReviewDeleteView(UserPassesTestMixin, DeleteView):
    model = Review
    raise_exception = True

    def test_func(self):
        review = self.get_object()
        return self.request.user.has_perm('review.delete_review') or self.request.user == review.author

    def delete(self, request, *args, **kwargs):
        review = self.get_object()
        messenger(
            MESSAGES.DELETE_REVIEW,
            user=request.user,
            request=request,
            source=review.submission,
            related=review,
        )
        response = super().delete(request, *args, **kwargs)
        return response

    def get_success_url(self):
        review = self.get_object()
        return reverse_lazy('funds:submissions:detail', args=(review.submission.id,))
