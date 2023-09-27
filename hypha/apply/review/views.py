from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.loader import get_template
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)
from wagtail.blocks import RichTextBlock

from hypha.apply.activity.messaging import MESSAGES, messenger
from hypha.apply.funds.models import ApplicationSubmission, AssignedReviewers
from hypha.apply.funds.workflow import INITIAL_STATE
from hypha.apply.review.blocks import RecommendationBlock, RecommendationCommentsBlock
from hypha.apply.review.forms import ReviewModelForm, ReviewOpinionForm
from hypha.apply.stream_forms.models import BaseStreamForm
from hypha.apply.users.decorators import staff_required
from hypha.apply.utils.image import generate_image_tag
from hypha.apply.utils.views import CreateOrUpdateView

from .models import Review, ReviewOpinion
from .options import DISAGREE


def get_fields_for_stage(submission, user=None):
    forms = submission.get_from_parent("review_forms").all()
    external_review_forms = submission.get_from_parent("external_review_forms").all()

    # Use ExternalReviewForm if submission's stage has external review and external review form is attached to fund.
    # ExternalReviewForm is only for non-staff reviewers(external reviewers)
    if submission.stage.has_external_review and external_review_forms:
        if user and not user.is_apply_staff:
            forms = external_review_forms

    index = submission.workflow.stages.index(submission.stage)
    try:
        return forms[index].form.form_fields
    except IndexError:
        return forms[0].form.form_fields


@method_decorator(login_required, name="dispatch")
class ReviewEditView(UserPassesTestMixin, BaseStreamForm, UpdateView):
    submission_form_class = ReviewModelForm
    model = Review
    template_name = "review/review_edit_form.html"
    raise_exception = True

    def test_func(self):
        review = self.get_object()
        return (
            self.request.user.has_perm("review.change_review")
            or self.request.user == review.author.reviewer
        )

    def get_context_data(self, **kwargs):
        review = self.get_object()
        return super().get_context_data(
            submission=review.submission, title=_("Edit Review"), **kwargs
        )

    def get_defined_fields(self):
        """Retrieve currently stored form_fields, if it exists, else retrieve it from the form configured
        in the rounds/lab of the submission.

        This ensures editing of submitted review is not affected by the changes to the original review forms.
        """
        review = self.get_object()
        return review.form_fields or get_fields_for_stage(
            review.submission, user=self.request.user
        )

    def get_form_kwargs(self):
        review = self.get_object()
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["submission"] = review.submission

        if self.object:
            kwargs["initial"] = self.object.form_data

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

        # Automatic workflow actions.
        review_workflow_actions(self.request, review.submission)

        return response

    def get_success_url(self):
        review = self.get_object()
        return reverse_lazy("funds:submissions:detail", args=(review.submission.id,))


@method_decorator(login_required, name="dispatch")
class ReviewCreateOrUpdateView(BaseStreamForm, CreateOrUpdateView):
    submission_form_class = ReviewModelForm
    model = Review
    template_name = "review/review_form.html"

    def get_object(self, queryset=None):
        return self.model.objects.get(
            submission=self.submission, author__reviewer=self.request.user
        )

    def dispatch(self, request, *args, **kwargs):
        self.submission = get_object_or_404(
            ApplicationSubmission, id=self.kwargs["submission_pk"]
        )

        if not self.submission.phase.permissions.can_review(
            request.user
        ) or not self.submission.has_permission_to_review(request.user):
            raise PermissionDenied()

        if self.request.POST and self.submission.reviewed_by(request.user):
            return self.get(request, *args, **kwargs)

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        has_submitted_review = self.submission.reviewed_by(self.request.user)
        return super().get_context_data(
            submission=self.submission,
            has_submitted_review=has_submitted_review,
            title=_("Update Review draft") if self.object else _("Create Review"),
            **kwargs,
        )

    def get_defined_fields(self):
        return get_fields_for_stage(self.submission, user=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["submission"] = self.submission

        if self.object:
            kwargs["initial"] = self.object.form_data

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
            review_workflow_actions(self.request, self.submission)

        return response

    def get_success_url(self):
        return self.submission.get_absolute_url()


def review_workflow_actions(request, submission):
    submission_stepped_phases = submission.workflow.stepped_phases
    transition_after = settings.TRANSITION_AFTER_REVIEWS
    action = None
    if transition_after and submission.status == INITIAL_STATE:
        # Automatically transition the application to "Internal review".
        action = submission_stepped_phases[2][0].name
    elif transition_after and submission.status == "proposal_discussion":
        # Automatically transition the proposal to "Internal review".
        action = "proposal_internal_review"
    elif (
        transition_after
        and submission.status == submission_stepped_phases[2][0].name
        and submission.reviews.count() >= transition_after
    ):
        # Automatically transition the application to "Ready for discussion".
        action = submission_stepped_phases[3][0].name
    elif (
        transition_after
        and submission.status == "ext_external_review"
        and submission.reviews.by_reviewers().count() >= transition_after
    ):
        # Automatically transition the application to "Ready for discussion".
        action = "ext_post_external_review_discussion"
    elif (
        transition_after
        and submission.status == "com_external_review"
        and submission.reviews.by_reviewers().count() >= transition_after
    ):
        # Automatically transition the application to "Ready for discussion".
        action = "com_post_external_review_discussion"
    elif (
        transition_after
        and submission.status == "external_review"
        and submission.reviews.by_reviewers().count() >= transition_after
    ):
        # Automatically transition the proposal to "Ready for discussion".
        action = "post_external_review_discussion"

    # If action is set run perform_transition().
    if action:
        try:
            submission.perform_transition(
                action,
                request.user,
                request=request,
                notify=False,
            )
        except (PermissionDenied, KeyError):
            pass


class ReviewDisplay(UserPassesTestMixin, DetailView):
    model = Review
    raise_exception = True

    def get_context_data(self, **kwargs):
        review = self.get_object()
        if review.author.reviewer != self.request.user:
            consensus_form = ReviewOpinionForm(
                instance=review.opinions.filter(
                    author__reviewer=self.request.user
                ).first(),
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

        if user.is_apply_staff:
            return True

        if user == author:
            return True

        if user.is_reviewer and review.reviewer_visibility:
            return True

        if (
            user.is_community_reviewer
            and submission.community_review
            and review.reviewer_visibility
            and submission.user != user
        ):
            return True

        return False

    def dispatch(self, request, *args, **kwargs):
        review = self.get_object()

        if review.is_draft:
            return HttpResponseRedirect(
                reverse_lazy(
                    "apply:submissions:reviews:form", args=(review.submission.id,)
                )
            )

        return super().dispatch(request, *args, **kwargs)


class ReviewOpinionFormView(UserPassesTestMixin, CreateView):
    template_name = "review/review_detail.html"
    form_class = ReviewOpinionForm
    model = Review
    raise_exception = True

    def get_form_kwargs(self):
        self.object = self.get_object()
        kwargs = super().get_form_kwargs()
        instance = kwargs["instance"]
        kwargs["instance"] = instance.opinions.filter(
            author__reviewer=self.request.user
        ).first()
        return kwargs

    def test_func(self):
        review = self.get_object()
        user = self.request.user
        author = review.author.reviewer
        submission = review.submission

        if user.is_apply_staff:
            return True

        if user == author:
            return False

        if user.is_reviewer and review.reviewer_visibility:
            return True

        if (
            user.is_community_reviewer
            and submission.community_review
            and review.reviewer_visibility
            and submission.user != user
        ):
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
            return HttpResponseRedirect(
                reverse_lazy(
                    "apply:submissions:reviews:form", args=(self.review.submission.pk,)
                )
            )
        else:
            return response

    def get_success_url(self):
        return self.review.get_absolute_url()


@method_decorator(login_required, name="dispatch")
class ReviewDetailView(DetailView):
    def get(self, request, *args, **kwargs):
        view = ReviewDisplay.as_view()
        return view(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        view = ReviewOpinionFormView.as_view()
        return view(request, *args, **kwargs)


@method_decorator(staff_required, name="dispatch")
class ReviewListView(ListView):
    model = Review

    def get_queryset(self):
        self.submission = get_object_or_404(
            ApplicationSubmission, id=self.kwargs["submission_pk"]
        )
        self.queryset = self.model.objects.filter(
            submission=self.submission, is_draft=False
        )
        return super().get_queryset()

    def should_display(self, field):
        return not isinstance(
            field.block,
            (RecommendationBlock, RecommendationCommentsBlock, RichTextBlock),
        )

    def get_context_data(self, **kwargs):
        review_data = {}

        # Add the header rows
        review_data["title"] = {"question": "", "answers": []}
        review_data["opinions"] = {"question": "Opinions", "answers": []}
        review_data["score"] = {"question": "Overall Score", "answers": []}
        review_data["recommendation"] = {"question": "Recommendation", "answers": []}
        review_data["revision"] = {"question": "Revision", "answers": []}
        review_data["comments"] = {"question": "Comments", "answers": []}

        responses = self.object_list.count()
        ordered_reviewers = (
            AssignedReviewers.objects.filter(submission=self.submission)
            .reviewed()
            .review_order()
        )

        reviews = {review.author: review for review in self.object_list}
        for i, reviewer in enumerate(ordered_reviewers):
            review = reviews[reviewer]
            author = '<a href="{}"><span>{}</span></a>'.format(
                review.get_absolute_url(), review.author
            )
            if review.author.role:
                author += generate_image_tag(review.author.role.icon, "12x12")
            author = f"<div>{author}</div>"

            review_data["title"]["answers"].append(author)
            opinions_template = get_template(
                "review/includes/review_opinions_list.html"
            )
            opinions_html = opinions_template.render(
                {"opinions": review.opinions.select_related("author").all()}
            )
            review_data["opinions"]["answers"].append(opinions_html)
            review_data["score"]["answers"].append(review.get_score_display)
            review_data["recommendation"]["answers"].append(
                review.get_recommendation_display()
            )
            review_data["comments"]["answers"].append(
                review.get_comments_display(include_question=False)
            )
            if review.for_latest:
                revision = "Current"
            else:
                revision = '<a href="{}">Compare</a>'.format(review.get_compare_url())
            review_data["revision"]["answers"].append(revision)

            for field_id in review.fields:
                field = review.field(field_id)
                data = review.data(field_id)
                if self.should_display(field):
                    question = field.value["field_label"]
                    review_data.setdefault(
                        field.id, {"question": question, "answers": [""] * responses}
                    )
                    review_data[field.id]["answers"][i] = field.block.render(
                        None, {"data": data}
                    )

        return super().get_context_data(
            submission=self.submission, review_data=review_data, **kwargs
        )


@method_decorator(login_required, name="dispatch")
class ReviewDeleteView(UserPassesTestMixin, DeleteView):
    model = Review
    raise_exception = True

    def test_func(self):
        review = self.get_object()
        return (
            self.request.user.has_perm("review.delete_review")
            or self.request.user == review.author.reviewer
        )

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
        return reverse_lazy("funds:submissions:detail", args=(review.submission.id,))


@method_decorator(login_required, name="dispatch")
class ReviewOpinionDeleteView(DeleteView):
    model = ReviewOpinion
    raise_exception = True

    def dispatch(self, request, *args, **kwargs):
        self.review_opinion = self.get_object()
        if self.request.user != self.review_opinion.author.reviewer:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        messenger(
            MESSAGES.DELETE_REVIEW_OPINION,
            user=request.user,
            request=request,
            source=self.review_opinion.review.submission,
            related=self.review_opinion,
        )
        response = super().delete(request, *args, **kwargs)
        return response

    def get_success_url(self):
        review = self.review_opinion.review
        return reverse_lazy("funds:submissions:detail", args=(review.submission.id,))
