import json
from copy import copy
from typing import Generator, Tuple

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import (
    login_required,
    user_passes_test,
)
from django.core.exceptions import PermissionDenied
from django.forms import BaseModelForm
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseRedirect,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views import View
from django.views.decorators.http import require_http_methods
from django.views.generic import (
    UpdateView,
)
from django_file_form.models import PlaceholderUploadedFile
from django_htmx.http import (
    HttpResponseClientRedirect,
    HttpResponseClientRefresh,
)

from hypha.apply.activity.messaging import MESSAGES, messenger
from hypha.apply.determinations.views import (
    DeterminationCreateOrUpdateView,
)
from hypha.apply.projects.forms import ProjectCreateForm
from hypha.apply.projects.models.project import PROJECT_STATUS_CHOICES
from hypha.apply.todo.options import PROJECT_WAITING_PF, PROJECT_WAITING_SOW
from hypha.apply.todo.views import add_task_to_user
from hypha.apply.users.decorators import (
    is_apply_staff,
    staff_required,
)
from hypha.apply.utils.views import (
    ViewDispatcher,
)

from .. import services
from ..forms import (
    ProgressSubmissionForm,
    UpdateMetaTermsForm,
    UpdatePartnersForm,
    UpdateReviewersForm,
    UpdateSubmissionLeadForm,
)
from ..models import (
    ApplicationSubmission,
)
from ..permissions import (
    has_permission,
)
from ..workflows.constants import (
    DRAFT_STATE,
    STAGE_CHANGE_ACTIONS,
)

User = get_user_model()


class BaseSubmissionEditView(UpdateView):
    """
    Converts the data held on the submission into an editable format and knows how to save
    that back to the object. Shortcuts the normal update view save approach
    """

    model = ApplicationSubmission

    def render_preview(self, request: HttpRequest, form: BaseModelForm) -> HttpResponse:
        """Gets a rendered preview of a form

        Creates a new revision on the `ApplicationSubmission`, removes the
        forms temporary files

        Args:
            request:
                Request used to trigger the preview to be used in the render
            form:
                Form to be rendered

        Returns:
            An `HttpResponse` containing a preview of the given form
        """

        self.object.create_revision(draft=True, by=request.user)
        messages.success(self.request, _("Draft saved"))

        # Required for django-file-form: delete temporary files for the new files
        # uploaded while edit.
        form.delete_temporary_files()

        context = self.get_context_data()
        return render(request, "funds/application_preview.html", context)

    def dispatch(self, request, *args, **kwargs):
        permission, _ = has_permission(
            "submission_edit",
            request.user,
            object=self.get_object(),
            raise_exception=True,
        )
        return super().dispatch(request, *args, **kwargs)

    def buttons(
        self,
    ) -> Generator[Tuple[str, str, str], Tuple[str, str, str], Tuple[str, str, str]]:
        """The buttons to be presented to the in the EditView

        Returns:
            A generator returning a tuple strings in the format of:
            (<button type>, <button styling>, <button label>)
        """
        if settings.SUBMISSION_PREVIEW_REQUIRED:
            yield ("preview", "primary", _("Preview and submit"))
            yield ("save", "white", _("Save draft"))
        else:
            yield ("submit", "primary", _("Submit"))
            yield ("save", "white", _("Save draft"))
            yield ("preview", "white", _("Preview"))

    def get_object_fund_current_round(self):
        assigned_fund = self.object.round.get_parent().specific
        if assigned_fund.open_round:
            return assigned_fund.open_round
        return False

    def get_on_submit_transition(self, user):
        """Gets the transition that should be triggered when a form is submitted.

        Checks all available status transitions for the current user and returns the first
        one that has trigger_on_submit=True in its custom settings.

        Returns:
            dict: The transition configuration dictionary with trigger_on_submit=True,
                or None if no matching transition is found.
        """
        return next(
            (
                t
                for t in self.object.get_available_user_status_transitions(user)
                if t.custom.get("trigger_on_submit", False)
            ),
            None,
        )

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        """Handle the form returned from a `SubmissionEditView`.

        Determine whether to return a form preview, draft the new edits,
        or submit and transition the `ApplicationSubmission` object

        Args:
            form: The valid form

        Returns:
            An `HttpResponse` depending on the actions taken in the edit view
        """

        self.object.form_data = form.cleaned_data

        is_draft = self.object.status == DRAFT_STATE

        # Handle a preview or a save (aka a draft)
        if "preview" in self.request.POST:
            return self.render_preview(self.request, form)

        if "save" in self.request.POST:
            return self.save_draft_and_refresh_page(form=form)

        # Handle an application being submitted from a DRAFT_STATE. This includes updating submit_time
        if is_draft and "submit" in self.request.POST:
            self.object.submit_time = timezone.now()
            if self.object.round:
                current_round = self.get_object_fund_current_round()
                if current_round:
                    self.object.round = current_round
            self.object.save(update_fields=["submit_time", "round"])

        revision = self.object.create_revision(by=self.request.user)
        submitting_proposal = self.object.phase.name in STAGE_CHANGE_ACTIONS

        if submitting_proposal:
            messenger(
                MESSAGES.PROPOSAL_SUBMITTED,
                request=self.request,
                user=self.request.user,
                source=self.object,
            )
        elif revision and not self.object.status == DRAFT_STATE:
            messenger(
                MESSAGES.APPLICANT_EDIT,
                request=self.request,
                user=self.request.user,
                source=self.object,
                related=revision,
            )

        if "submit" in self.request.POST:
            if transition := self.get_on_submit_transition(self.request.user):
                notify = (
                    not (revision or submitting_proposal)
                    or self.object.status == DRAFT_STATE,
                )
                self.object.perform_transition(
                    transition.target,
                    self.request.user,
                    request=self.request,
                    notify=notify,  # Use the other notification
                )

        # Required for django-file-form: delete temporary files for the new files
        # uploaded while edit.
        form.delete_temporary_files()
        return HttpResponseRedirect(self.get_success_url())

    def get_form_kwargs(self):
        """
        Returns the keyword arguments for instantiating the form.

        This method is called by the form mixin during form instantiation.
        It returns a dictionary of keyword arguments that will be passed to
        the form's constructor.

        Returns:
            dict: A dictionary of keyword arguments for the form constructor.
        """
        kwargs = super().get_form_kwargs()
        instance = kwargs.pop("instance").from_draft()
        initial = instance.raw_data
        for field_id in instance.file_field_ids:
            initial.pop(field_id + "-uploads", False)
            initial[field_id] = self.get_placeholder_file(
                instance.raw_data.get(field_id)
            )
        kwargs["initial"] = initial
        return kwargs

    def get_placeholder_file(self, initial_file):
        if not isinstance(initial_file, list):
            return PlaceholderUploadedFile(
                initial_file.filename, size=initial_file.size, file_id=initial_file.name
            )
        return [
            PlaceholderUploadedFile(f.filename, size=f.size, file_id=f.name)
            for f in initial_file
        ]

    def save_draft_and_refresh_page(self, form) -> HttpResponseRedirect:
        self.object.create_revision(draft=True, by=self.request.user)
        form.delete_temporary_files()
        messages.success(self.request, _("Draft saved"))
        return HttpResponseRedirect(
            reverse_lazy("funds:submissions:edit", args=(self.object.id,))
        )

    def get_context_data(self, **kwargs):
        return super().get_context_data(buttons=self.buttons(), **kwargs)

    def get_form_class(self):
        """
        Returns the form class for the view.

        This method is called by the view during form instantiation. It returns
        the form class that will be used to render the form.

        When trying to save as draft, this method will return a version of form
        class that doesn't validate required fields while saving.

        Returns:
            class: The form class for the view.
        """
        is_draft = True if "save" in self.request.POST else False
        form_fields = self.object.get_form_fields(
            draft=is_draft, form_data=self.object.raw_data, user=self.request.user
        )
        return type(
            "WagtailStreamForm", (self.object.submission_form_class,), form_fields
        )


@method_decorator(staff_required, name="dispatch")
class AdminSubmissionEditView(BaseSubmissionEditView):
    def buttons(
        self,
    ) -> Generator[Tuple[str, str, str], Tuple[str, str, str], Tuple[str, str, str]]:
        """The buttons to be presented in the `AdminSubmissionEditView`

        Admins shouldn't be required to preview, but should have the option.

        Returns:
            A generator returning a tuple strings in the format of:
            (<button type>, <button styling>, <button label>)
        """
        yield ("submit", "primary", _("Submit"))
        yield ("save", "white", _("Save draft"))
        yield ("preview", "white", _("Preview"))


@method_decorator(login_required, name="dispatch")
class ApplicantSubmissionEditView(BaseSubmissionEditView):
    def dispatch(self, request, *args, **kwargs):
        submission = self.get_object()
        if (
            request.user != submission.user
            and not submission.co_applicants.filter(user=request.user).exists()
        ):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


@method_decorator(login_required, name="dispatch")
class PartnerSubmissionEditView(ApplicantSubmissionEditView):
    def dispatch(self, request, *args, **kwargs):
        submission = self.get_object()
        # If the requesting user submitted the application, return the Applicant view.
        # Partners may sometimes be applicants as well.
        partner_has_access = submission.partners.filter(pk=request.user.pk).exists()
        if not partner_has_access and submission.user != request.user:
            raise PermissionDenied
        return super(ApplicantSubmissionEditView, self).dispatch(
            request, *args, **kwargs
        )


class SubmissionEditView(ViewDispatcher):
    admin_view = AdminSubmissionEditView
    applicant_view = ApplicantSubmissionEditView
    reviewer_view = ApplicantSubmissionEditView
    partner_view = PartnerSubmissionEditView


@method_decorator(staff_required, name="dispatch")
class ProgressSubmissionView(View):
    def dispatch(self, request, *args, **kwargs):
        self.submission = get_object_or_404(ApplicationSubmission, id=kwargs.get("pk"))
        permission, reason = has_permission(
            "submission_action",
            request.user,
            object=self.submission,
            raise_exception=False,
        )
        if not permission:
            messages.warning(self.request, reason)
            return HttpResponseRedirect(self.submission.get_absolute_url())
        return super(ProgressSubmissionView, self).dispatch(request, *args, **kwargs)

    def get(self, *args, **kwargs):
        project_creation_form = ProgressSubmissionForm(
            instance=self.submission, user=self.request.user
        )
        return render(
            self.request,
            "funds/modals/progress_form.html",
            context={
                "form": project_creation_form,
                "value": _("Progress"),
                "object": self.submission,
            },
        )

    def post(self, *args, **kwargs):
        form = ProgressSubmissionForm(
            self.request.POST, instance=self.submission, user=self.request.user
        )
        if form.is_valid():
            action = form.cleaned_data.get("action")
            redirect = DeterminationCreateOrUpdateView.should_redirect(
                self.request, self.submission, action
            )
            message_storage = messages.get_messages(self.request)
            if redirect:
                return HttpResponseClientRedirect(redirect.url, content=message_storage)

            self.submission.perform_transition(
                action, self.request.user, request=self.request
            )
            form.save()
            return HttpResponseClientRefresh()
        return render(
            self.request,
            "funds/modals/progress_form.html",
            context={"form": form, "value": _("Progress"), "object": self.submission},
            status=400,
        )


@method_decorator(staff_required, name="dispatch")
class CreateProjectView(View):
    def dispatch(self, request, *args, **kwargs):
        self.submission = get_object_or_404(ApplicationSubmission, id=kwargs.get("pk"))
        permission, reason = has_permission(
            "submission_action",
            request.user,
            object=self.submission,
            raise_exception=False,
        )
        if not permission:
            messages.warning(self.request, reason)
            return HttpResponseRedirect(self.submission.get_absolute_url())
        return super(CreateProjectView, self).dispatch(request, *args, **kwargs)

    def get(self, *args, **kwargs):
        project_creation_form = ProjectCreateForm(instance=self.submission)
        return render(
            self.request,
            "funds/modals/create_project_form.html",
            context={
                "form": project_creation_form,
                "value": _("Confirm"),
                "object": self.submission,
            },
        )

    def post(self, *args, **kwargs):
        form = ProjectCreateForm(self.request.POST, instance=self.submission)
        if form.is_valid():
            project = form.save()

            readable_project_status = next(
                status[1]
                for status in PROJECT_STATUS_CHOICES
                if status[0] == project.status
            )

            # Record activity
            messenger(
                MESSAGES.CREATED_PROJECT,
                request=self.request,
                user=self.request.user,
                status=readable_project_status,
                source=project,
                related=project.submission,
            )
            # add task for staff to add PAF to the project
            add_task_to_user(
                code=PROJECT_WAITING_PF,
                user=project.lead,
                related_obj=project,
            )
            if self.submission.page.specific.sow_forms.first():
                # Add SOW task if one exists on the parent
                add_task_to_user(
                    code=PROJECT_WAITING_SOW,
                    user=project.lead,
                    related_obj=project,
                )
            return HttpResponseClientRedirect(project.get_absolute_url())
        return render(
            self.request,
            "funds/modals/create_project_form.html",
            context={"form": form, "value": _("Confirm"), "object": self.submission},
            status=400,
        )


@login_required
@user_passes_test(is_apply_staff)
@require_http_methods(["GET", "POST"])
def htmx_archive_unarchive_submission(request, pk):
    submission = get_object_or_404(ApplicationSubmission, id=pk)
    permission, reason = has_permission(
        "archive_alter", request.user, object=submission, raise_exception=False
    )
    if not permission:
        return HttpResponse(reason)

    if submission.is_archive:
        template = "funds/includes/modal_unarchive_submission_confirm.html"
    else:
        template = "funds/includes/modal_archive_submission_confirm.html"

    if request.method == "POST":
        if submission.is_archive:
            submission.is_archive = False
            submission.save()
            messenger(
                MESSAGES.UNARCHIVE_SUBMISSION,
                request=request,
                user=request.user,
                source=submission,
            )
        else:
            submission.is_archive = True
            submission.save()
            messenger(
                MESSAGES.ARCHIVE_SUBMISSION,
                request=request,
                user=request.user,
                source=submission,
            )

        return redirect(submission.get_absolute_url())

    return render(
        request,
        template,
        context={"submission": submission},
    )


@method_decorator(staff_required, name="dispatch")
class UpdateLeadView(View):
    model = ApplicationSubmission
    form_class = UpdateSubmissionLeadForm
    context_name = "lead_form"
    template = "funds/modals/update_lead_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.object = get_object_or_404(ApplicationSubmission, id=kwargs.get("pk"))
        permission, reason = has_permission(
            "submission_action", request.user, object=self.object, raise_exception=False
        )
        if not permission:
            messages.warning(self.request, reason)
            return HttpResponseRedirect(self.object.get_absolute_url())
        return super().dispatch(request, *args, **kwargs)

    def get(self, *args, **kwargs):
        lead_form = UpdateSubmissionLeadForm(instance=self.object)
        return render(
            self.request,
            self.template,
            context={
                "form": lead_form,
                "value": _("Update"),
                "object": self.object,
            },
        )

    def post(self, *args, **kwargs):
        form = UpdateSubmissionLeadForm(self.request.POST, instance=self.object)
        old_lead = copy(self.object.lead)
        if form.is_valid():
            form.save()
            messenger(
                MESSAGES.UPDATE_LEAD,
                request=self.request,
                user=self.request.user,
                source=form.instance,
                related=old_lead,
            )
            return HttpResponse(
                status=204,
                headers={
                    "HX-Trigger": json.dumps(
                        {
                            "leadUpdated": None,
                            "showMessage": _("Submission Lead updated."),
                        }
                    ),
                },
            )
        return render(
            self.request,
            self.template,
            context={"form": form, "value": _("Update"), "object": self.object},
            status=400,
        )


@method_decorator(staff_required, name="dispatch")
class UpdateReviewersView(View):
    def dispatch(self, request, *args, **kwargs):
        self.submission = get_object_or_404(ApplicationSubmission, id=kwargs.get("pk"))
        permission, reason = has_permission(
            "submission_action",
            request.user,
            object=self.submission,
            raise_exception=False,
        )
        if not permission:
            messages.warning(self.request, reason)
            return HttpResponseRedirect(self.submission.get_absolute_url())
        return super(UpdateReviewersView, self).dispatch(request, *args, **kwargs)

    def get(self, *args, **kwargs):
        reviewer_form = UpdateReviewersForm(
            user=self.request.user, instance=self.submission
        )
        return render(
            self.request,
            "funds/includes/update_reviewer_form.html",
            context={
                "form": reviewer_form,
                "value": _("Update"),
                "object": self.submission,
            },
        )

    def post(self, *args, **kwargs):
        form = UpdateReviewersForm(
            self.request.POST, user=self.request.user, instance=self.submission
        )
        old_reviewers = {copy(reviewer) for reviewer in form.instance.assigned.all()}
        if form.is_valid():
            form.save()
            new_reviewers = set(form.instance.assigned.all())
            added = new_reviewers - old_reviewers
            removed = old_reviewers - new_reviewers
            messenger(
                MESSAGES.REVIEWERS_UPDATED,
                request=self.request,
                user=self.request.user,
                source=self.submission,
                added=added,
                removed=removed,
            )
            # Update submission status if needed.
            services.set_status_after_reviewers_assigned(
                submission=form.instance,
                updated_by=self.request.user,
                request=self.request,
            )
            return HttpResponse(
                status=204,
                headers={
                    "HX-Trigger": json.dumps(
                        {
                            "reviewerUpdated": None,
                            "showMessage": _("Reviewers updated."),
                        }
                    ),
                },
            )

        return render(
            self.request,
            "funds/includes/update_reviewer_form.html",
            context={"form": form, "value": _("Update"), "object": self.submission},
        )


@method_decorator(staff_required, name="dispatch")
class UpdatePartnersView(View):
    model = ApplicationSubmission
    form_class = UpdatePartnersForm
    context_name = "partner_form"
    template = "funds/modals/update_partner_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.submission = get_object_or_404(ApplicationSubmission, id=kwargs.get("pk"))
        permission, reason = has_permission(
            "submission_action",
            request.user,
            object=self.submission,
            raise_exception=False,
        )
        if not permission:
            messages.warning(self.request, reason)
            return HttpResponseRedirect(self.submission.get_absolute_url())
        return super(UpdatePartnersView, self).dispatch(request, *args, **kwargs)

    def get(self, *args, **kwargs):
        partner_form = UpdatePartnersForm(
            user=self.request.user, instance=self.submission
        )
        return render(
            self.request,
            self.template,
            context={
                "form": partner_form,
                "value": _("Update"),
                "object": self.submission,
            },
        )

    def post(self, *args, **kwargs):
        form = UpdatePartnersForm(
            self.request.POST, user=self.request.user, instance=self.submission
        )
        old_partners = set(self.submission.partners.all())
        if form.is_valid():
            form.save()
            new_partners = set(form.instance.partners.all())

            added = new_partners - old_partners
            removed = old_partners - new_partners
            messenger(
                MESSAGES.PARTNERS_UPDATED,
                request=self.request,
                user=self.request.user,
                source=self.submission,
                added=added,
                removed=removed,
            )

            messenger(
                MESSAGES.PARTNERS_UPDATED_PARTNER,
                request=self.request,
                user=self.request.user,
                source=self.submission,
                added=added,
                removed=removed,
            )

            return HttpResponse(
                status=204,
                headers={
                    "HX-Trigger": json.dumps(
                        {
                            "partnerUpdated": None,
                            "showMessage": _("Partners updated successfully."),
                        }
                    ),
                },
            )

        return render(
            self.request,
            self.template,
            context={"form": form, "value": _("Update"), "object": self.submission},
            status=400,
        )


@method_decorator(staff_required, name="dispatch")
class UpdateMetaTermsView(View):
    template = "funds/modals/update_meta_terms_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.submission = get_object_or_404(ApplicationSubmission, id=kwargs.get("pk"))
        permission, reason = has_permission(
            "submission_action",
            request.user,
            object=self.submission,
            raise_exception=False,
        )
        if not permission:
            messages.warning(self.request, reason)
            return HttpResponseRedirect(self.submission.get_absolute_url())
        return super(UpdateMetaTermsView, self).dispatch(request, *args, **kwargs)

    def get(self, *args, **kwargs):
        metaterms_form = UpdateMetaTermsForm(
            user=self.request.user, instance=self.submission
        )
        return render(
            self.request,
            self.template,
            context={
                "form": metaterms_form,
                "value": _("Update"),
                "object": self.submission,
            },
        )

    def post(self, *args, **kwargs):
        form = UpdateMetaTermsForm(
            self.request.POST, instance=self.submission, user=self.request.user
        )
        if form.is_valid():
            form.save()

            return HttpResponse(
                status=204,
                headers={
                    "HX-Trigger": json.dumps(
                        {
                            "metaTermsUpdated": None,
                            "showMessage": _("Meta terms updated successfully."),
                        }
                    ),
                },
            )
        return render(
            self.request,
            self.template,
            context={"form": form, "value": _("Update"), "object": self.submission},
            status=400,
        )
