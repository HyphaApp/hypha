from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import DeleteView
from rolepermissions.checkers import has_object_permission

from hypha.apply.activity.messaging import MESSAGES, messenger
from hypha.apply.activity.models import Event
from hypha.apply.funds.forms import DeleteSubmissionForm

from ..models import ApplicationSubmission, ApplicationSubmissionSkeleton
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
    form_class = DeleteSubmissionForm

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

        message = MESSAGES.DELETE_SUBMISSION

        success_popup_message = _("Submission deleted.")

        if (
            form.cleaned_data.get("anon_or_delete") == "ANONYMIZE"
            and submission.status != DRAFT_STATE
        ):
            ApplicationSubmissionSkeleton.from_submission(submission)
            message = MESSAGES.ANONYMIZE_SUBMISSION
            success_popup_message = _("Submission anonymized.")

        # Delete NEW_SUBMISSION & COMMENT events for this particular submission, if any.
        # Otherwise, the submission deletion will fail.
        Event.objects.filter(
            type__in=[MESSAGES.NEW_SUBMISSION, MESSAGES.COMMENT],
            object_id=submission.id,
        ).delete()

        # delete submission and redirect to success url
        response = super().form_valid(form)

        # Handle messaging last to ensure everything is successful
        # Notify unless author delete own draft.
        if submission.status != DRAFT_STATE and submission.user != self.request.user:
            messenger(
                message,
                user=self.request.user,
                request=self.request,
                source=submission,
            )

        messages.success(self.request, success_popup_message)

        return response
