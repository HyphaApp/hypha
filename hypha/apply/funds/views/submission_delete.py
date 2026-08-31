from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import DeleteView
from rolepermissions.checkers import has_object_permission

from hypha.apply.activity.messaging import MESSAGES, messenger
from hypha.apply.activity.models import Event

from ..models import AnonymizedSubmission, ApplicationSubmission
from ..workflows.constants import DRAFT_STATE


class SubmissionAnonymizeView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """View for anonymizing a submission via confirmation modal."""

    model = ApplicationSubmission
    template_name = "funds/applicationsubmission_confirm_anonymize.html"

    def test_func(self):
        return has_object_permission(
            "delete_submission", self.request.user, obj=self.get_object()
        )

    def get_success_url(self):
        return reverse_lazy("funds:submissions:list")

    def form_valid(self, form):
        submission = self.get_object()

        AnonymizedSubmission.from_submission(submission)

        Event.objects.filter(
            type__in=[MESSAGES.NEW_SUBMISSION, MESSAGES.COMMENT],
            object_id=submission.id,
        ).delete()

        if submission.status != DRAFT_STATE:
            messenger(
                MESSAGES.ANONYMIZE_SUBMISSION,
                user=self.request.user,
                request=self.request,
                source=submission,
            )

        messages.success(self.request, _("Submission anonymized."))

        return super().form_valid(form)


class SubmissionDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    View for deleting submissions with confirmation modal.

    After successful deletion:
    - Redirects applicants to their dashboard
    - Redirects staff to the submissions list
    - Creates delete notification unless author deleting own draft
    """

    model = ApplicationSubmission

    def test_func(self):
        return has_object_permission(
            "delete_submission", self.request.user, obj=self.get_object()
        )

    def get_success_url(self):
        if self.request.user.is_applicant:
            return reverse_lazy("dashboard:dashboard")
        return reverse_lazy("funds:submissions:list")

    def form_valid(self, form):
        submission = self.get_object()

        # Notify unless author delete own draft.
        if submission.status != DRAFT_STATE and submission.user != self.request.user:
            messenger(
                MESSAGES.DELETE_SUBMISSION,
                user=self.request.user,
                request=self.request,
                source=submission,
            )

        # Delete NEW_SUBMISSION & COMMENT events for this particular submission, if any.
        # Otherwise, the submission deletion will fail.
        Event.objects.filter(
            type__in=[MESSAGES.NEW_SUBMISSION, MESSAGES.COMMENT],
            object_id=submission.id,
        ).delete()

        # delete submission and redirect to success url
        return super().form_valid(form)
