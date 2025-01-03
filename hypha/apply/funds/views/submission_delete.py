from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import DeleteView
from rolepermissions.checkers import has_object_permission

from hypha.apply.activity.messaging import MESSAGES, messenger
from hypha.apply.activity.models import Event

from ..models import ApplicationSubmission
from ..workflows.constants import DRAFT_STATE


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

        # Delete NEW_SUBMISSION event for this particular submission, if any.
        # Otherwise, the submission deletion will fail.
        Event.objects.filter(
            type=MESSAGES.NEW_SUBMISSION, object_id=submission.id
        ).delete()

        # delete submission and redirect to success url
        return super().form_valid(form)
