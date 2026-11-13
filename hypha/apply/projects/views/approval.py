import datetime
import io

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, render
from django.template.loader import get_template
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.text import slugify
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import (
    DetailView,
    UpdateView,
)
from django.views.generic.detail import SingleObjectMixin
from django_htmx.http import (
    HttpResponseClientRefresh,
)

from hypha.apply.activity.adapters.utils import get_users_for_groups
from hypha.apply.activity.messaging import MESSAGES, messenger
from hypha.apply.activity.models import ACTION, COMMENT, TEAM, Activity
from hypha.apply.todo.options import (
    PAF_REQUIRED_CHANGES,
    PAF_WAITING_APPROVAL,
    PAF_WAITING_ASSIGNEE,
    PROJECT_SUBMIT_PAF,
    PROJECT_WAITING_CONTRACT,
)
from hypha.apply.todo.views import (
    add_task_to_user,
    add_task_to_user_group,
    remove_tasks_for_user,
    remove_tasks_for_user_group,
)
from hypha.apply.users.decorators import (
    staff_or_finance_or_contracting_required,
    staff_required,
)
from hypha.apply.users.roles import CONTRACTING_GROUP_NAME
from hypha.apply.utils.models import PDFPageSettings
from hypha.apply.utils.pdfs import render_as_pdf

from ..forms import (
    ApproversForm,
    AssignApproversForm,
    ChangePAFStatusForm,
    SetPendingForm,
    SkipPAFApprovalProcessForm,
)
from ..models.project import (
    APPROVE,
    CONTRACTING,
    DRAFT,
    INTERNAL_APPROVAL,
    REQUEST_CHANGE,
    DocumentCategory,
    PAFApprovals,
    Project,
    ProjectSettings,
)
from ..permissions import has_permission
from ..utils import (
    get_paf_status_display,
)
from .mixins import ProjectByIdMixin


@method_decorator(staff_required, name="dispatch")
class SendForApprovalView(ProjectByIdMixin, View):
    form_class = SetPendingForm
    model = Project
    template_name = "application_projects/modals/send_for_approval.html"

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        # permission check
        return super().dispatch(request, *args, **kwargs)

    def get(self, *args, **kwargs):
        form = self.form_class(instance=self.object)
        project_settings = ProjectSettings.for_request(self.request)
        return render(
            self.request,
            self.template_name,
            context={
                "form": form,
                "project_settings": project_settings,
                "paf_approvals": PAFApprovals.objects.filter(project=self.object),
                "remaining_document_categories": DocumentCategory.objects.filter(
                    ~Q(packet_files__project=self.object)
                ),
                "object": self.object,
            },
        )

    def post(self, *args, **kwargs):
        form = self.form_class(
            self.request.POST, user=self.request.user, instance=self.object
        )
        project_settings = ProjectSettings.for_request(self.request)
        if form.is_valid():
            project = self.object
            old_stage = project.status
            form.save()

            # remove PAF submission task for staff group
            remove_tasks_for_user(
                code=PROJECT_SUBMIT_PAF,
                user=self.object.lead,
                related_obj=self.object,
            )

            # remove PAF rejection task for staff if exists
            remove_tasks_for_user(
                code=PAF_REQUIRED_CHANGES,
                user=self.object.lead,
                related_obj=self.object,
            )

            paf_approvals = self.object.paf_approvals.filter(approved=False)

            if project_settings.paf_approval_sequential:
                if paf_approvals:
                    user = paf_approvals.first().user
                    if user:
                        # notify only if first user/approver is updated
                        messenger(
                            MESSAGES.SEND_FOR_APPROVAL,
                            request=self.request,
                            user=self.request.user,
                            source=self.object,
                        )
                        messenger(
                            MESSAGES.APPROVE_PAF,
                            request=self.request,
                            user=self.request.user,
                            source=self.object,
                            related=[paf_approvals.first()],
                        )
                        # add PAF waiting approval task for paf_approval user
                        add_task_to_user(
                            code=PAF_WAITING_APPROVAL,
                            user=user,
                            related_obj=self.object,
                        )
                    else:
                        messenger(
                            MESSAGES.ASSIGN_PAF_APPROVER,
                            request=self.request,
                            user=self.request.user,
                            source=self.object,
                        )
                        # add PAF waiting assignee task for paf_approval reviewer_roles
                        add_task_to_user_group(
                            code=PAF_WAITING_ASSIGNEE,
                            user_group=paf_approvals.first().paf_reviewer_role.user_roles.all(),
                            related_obj=self.object,
                        )
            else:
                if paf_approvals.filter(user__isnull=False).exists():
                    messenger(
                        MESSAGES.SEND_FOR_APPROVAL,
                        request=self.request,
                        user=self.request.user,
                        source=self.object,
                    )
                    messenger(
                        MESSAGES.APPROVE_PAF,
                        request=self.request,
                        user=self.request.user,
                        source=self.object,
                        related=paf_approvals.filter(user__isnull=False),
                    )
                    # add PAF waiting approval task for paf_approvals users
                    for paf_approval in paf_approvals.filter(user__isnull=False):
                        add_task_to_user(
                            code=PAF_WAITING_APPROVAL,
                            user=paf_approval.user,
                            related_obj=self.object,
                        )
                if paf_approvals.filter(user__isnull=True).exists():
                    messenger(
                        MESSAGES.ASSIGN_PAF_APPROVER,
                        request=self.request,
                        user=self.request.user,
                        source=self.object,
                    )
                    # add PAF waiting assignee task for paf_approvals reviewer_roles
                    for paf_approval in paf_approvals.filter(user__isnull=True):
                        add_task_to_user_group(
                            code=PAF_WAITING_ASSIGNEE,
                            user_group=paf_approval.paf_reviewer_role.user_roles.all(),
                            related_obj=self.object,
                        )

            project.status = INTERNAL_APPROVAL
            project.save(update_fields=["status"])

            messenger(
                MESSAGES.PROJECT_TRANSITION,
                request=self.request,
                user=self.request.user,
                source=project,
                related=old_stage,
            )

            messages.success(self.request, _("PAF has been submitted for approval"))
            return HttpResponseClientRefresh()
        return render(
            self.request,
            self.template_name,
            context={
                "form": form,
                "project_settings": project_settings,
                "paf_approvals": PAFApprovals.objects.filter(project=self.object),
                "remaining_document_categories": DocumentCategory.objects.filter(
                    ~Q(packet_files__project=self.object)
                ),
                "object": self.object,
            },
        )


# PROJECT DOCUMENTS


@method_decorator(login_required, name="dispatch")
class SkipPAFApprovalProcessView(UpdateView):
    model = Project
    form_class = SkipPAFApprovalProcessForm

    def dispatch(self, request, *args, **kwargs):
        self.object = get_object_or_404(Project, id=kwargs.get("pk"))
        has_permission(
            "skip_pafapproval_process",
            request.user,
            object=self.object,
            raise_exception=True,
        )
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        project = self.object
        old_stage = project.status
        project.is_locked = True
        project.status = CONTRACTING
        super().form_valid(form)

        # remove PAF submission task for staff group
        remove_tasks_for_user(
            code=PROJECT_SUBMIT_PAF,
            user=self.object.lead,
            related_obj=self.object,
        )

        # remove PAF rejection task for staff if exists
        remove_tasks_for_user(
            code=PAF_REQUIRED_CHANGES,
            user=self.object.lead,
            related_obj=self.object,
        )

        messenger(
            MESSAGES.PROJECT_TRANSITION,
            request=self.request,
            user=self.request.user,
            source=self.object,
            related=old_stage,
        )
        # add project waiting contract task to staff/contracting groups
        if settings.STAFF_UPLOAD_CONTRACT:
            add_task_to_user(
                code=PROJECT_WAITING_CONTRACT,
                user=self.object.lead,
                related_obj=self.object,
            )
        else:
            add_task_to_user_group(
                code=PROJECT_WAITING_CONTRACT,
                user_group=Group.objects.filter(name=CONTRACTING_GROUP_NAME),
                related_obj=self.object,
            )
        return HttpResponseClientRefresh()


@method_decorator(login_required, name="dispatch")
class ChangePAFStatusView(View):
    form_class = ChangePAFStatusForm
    model = Project
    template_name = "application_projects/modals/pafstatus_update.html"

    def dispatch(self, request, *args, **kwargs):
        self.object = get_object_or_404(Project, pk=self.kwargs["pk"])
        has_permission(
            "paf_status_update",
            self.request.user,
            object=self.object,
            raise_exception=True,
            request=request,
        )
        return super().dispatch(request, *args, **kwargs)

    def get(self, *args, **kwargs):
        form = self.form_class(instance=self.object)
        return render(
            self.request,
            self.template_name,
            context={
                "form": form,
                "value": _("Update Status"),
                "object": self.object,
            },
        )

    def post(self, *args, **kwargs):
        form = self.form_class(self.request.POST, instance=self.object)
        if form.is_valid():
            form.save()
            message_kwargs = {}
            project_settings = ProjectSettings.for_request(self.request)
            paf_approval = self.request.user.paf_approvals.filter(
                project=self.object, approved=False
            ).first()
            if not paf_approval:
                # get paf project form for not-assigned case
                if project_settings.paf_approval_sequential:
                    paf_approval = self.object.paf_approvals.filter(
                        approved=False
                    ).first()
                else:
                    for approval in self.object.paf_approvals.filter(approved=False):
                        if self.request.user.id in [
                            role_user.id
                            for role_user in get_users_for_groups(
                                list(approval.paf_reviewer_role.user_roles.all()),
                                exact_match=True,
                            )
                        ]:
                            paf_approval = approval
                            break
                    else:
                        # should never be the case but still to avoid 500.
                        raise PermissionDenied(
                            _("User don't have project form approver roles")
                        )

            paf_status = form.cleaned_data.get("paf_status")

            paf_status_update_message = _(
                "Updated project form status to: {paf_status}"
            ).format(
                paf_status=get_paf_status_display(paf_status).lower(),
            )

            if form.cleaned_data["comment"]:
                comment = f'<p>"{form.cleaned_data["comment"]}"</p>'

                message = paf_status_update_message + comment

                comment_activity = Activity.objects.create(
                    user=self.request.user,
                    type=COMMENT,
                    source=self.object,
                    timestamp=timezone.now(),
                    message=message,
                    visibility=TEAM,
                )

                message_kwargs["comment_url"] = comment_activity.get_absolute_url()
            Activity.objects.create(
                user=self.request.user,
                type=ACTION,
                source=self.object,
                timestamp=timezone.now(),
                message=paf_status_update_message,
                visibility=TEAM,
            )

            if paf_status == REQUEST_CHANGE:
                old_stage = self.object.status
                self.object.status = DRAFT
                self.object.save(update_fields=["status"])
                paf_approval.save()

                # remove PAF waiting assignee/approval task for paf approval user/reviewer roles.
                if project_settings.paf_approval_sequential:
                    if paf_approval.user:
                        remove_tasks_for_user(
                            code=PAF_WAITING_APPROVAL,
                            user=paf_approval.user,
                            related_obj=self.object,
                        )
                    else:
                        remove_tasks_for_user_group(
                            code=PAF_WAITING_ASSIGNEE,
                            user_group=paf_approval.paf_reviewer_role.user_roles.all(),
                            related_obj=self.object,
                        )
                else:
                    for approval in self.object.paf_approvals.filter(approved=False):
                        if approval.user:
                            remove_tasks_for_user(
                                code=PAF_WAITING_APPROVAL,
                                user=approval.user,
                                related_obj=self.object,
                            )
                        else:
                            remove_tasks_for_user_group(
                                code=PAF_WAITING_ASSIGNEE,
                                user_group=approval.paf_reviewer_role.user_roles.all(),
                                related_obj=self.object,
                            )

                if not paf_approval.user:
                    paf_approval.user = self.request.user
                    paf_approval.save(update_fields=["user"])

                messenger(
                    MESSAGES.REQUEST_PROJECT_CHANGE,
                    request=self.request,
                    user=self.request.user,
                    source=self.object,
                    **message_kwargs,
                )
                messenger(
                    MESSAGES.PROJECT_TRANSITION,
                    request=self.request,
                    user=self.request.user,
                    source=self.object,
                    related=old_stage,
                )
                # add PAF required changes task to staff user group
                add_task_to_user(
                    code=PAF_REQUIRED_CHANGES,
                    user=self.object.lead,
                    related_obj=self.object,
                )

                messages.success(
                    self.request, _("Project form status has been updated")
                )
            elif paf_status == APPROVE:
                # remove task for paf approval user/user_group related to this paf_approval of project
                if paf_approval.user:
                    remove_tasks_for_user(
                        code=PAF_WAITING_APPROVAL,
                        user=paf_approval.user,
                        related_obj=self.object,
                    )
                else:
                    remove_tasks_for_user_group(
                        code=PAF_WAITING_ASSIGNEE,
                        user_group=paf_approval.paf_reviewer_role.user_roles.all(),
                        related_obj=self.object,
                    )
                paf_approval.approved = True
                paf_approval.approved_at = timezone.now()
                paf_approval.user = self.request.user
                paf_approval.save(update_fields=["approved", "approved_at", "user"])
                if project_settings.paf_approval_sequential:
                    # notify next approver
                    if self.object.paf_approvals.filter(approved=False).exists():
                        next_paf_approval = self.object.paf_approvals.filter(
                            approved=False
                        ).first()
                        if next_paf_approval.user:
                            messenger(
                                MESSAGES.APPROVE_PAF,
                                request=self.request,
                                user=self.request.user,
                                source=self.object,
                                related=[next_paf_approval],
                            )
                            # add PAF waiting approval task for next paf approval user
                            add_task_to_user(
                                code=PAF_WAITING_APPROVAL,
                                user=next_paf_approval.user,
                                related_obj=self.object,
                            )
                        else:
                            messenger(
                                MESSAGES.ASSIGN_PAF_APPROVER,
                                request=self.request,
                                user=self.request.user,
                                source=self.object,
                            )
                            # add PAF waiting assignee task for nex paf approval reviewer roles
                            add_task_to_user_group(
                                code=PAF_WAITING_ASSIGNEE,
                                user_group=next_paf_approval.paf_reviewer_role.user_roles.all(),
                                related_obj=self.object,
                            )
                messages.success(self.request, _("Project form has been approved"))

            if self.object.is_approved_by_all_paf_reviewers:
                old_stage = self.object.status
                self.object.is_locked = True
                self.object.status = CONTRACTING
                self.object.save(update_fields=["is_locked", "status"])

                messenger(
                    MESSAGES.PROJECT_TRANSITION,
                    request=self.request,
                    user=self.request.user,
                    source=self.object,
                    related=old_stage,
                )
                # add project waiting contract task to staff/contracting groups
                if settings.STAFF_UPLOAD_CONTRACT:
                    add_task_to_user(
                        code=PROJECT_WAITING_CONTRACT,
                        user=self.object.lead,
                        related_obj=self.object,
                    )
                else:
                    add_task_to_user_group(
                        code=PROJECT_WAITING_CONTRACT,
                        user_group=Group.objects.filter(name=CONTRACTING_GROUP_NAME),
                        related_obj=self.object,
                    )
            return HttpResponseClientRefresh()
        return render(
            self.request,
            self.template_name,
            context={
                "form": form,
                "value": _("Update Status"),
                "object": self.object,
            },
        )


@method_decorator(login_required, name="dispatch")
class UpdateAssignApproversView(View):
    form_class = AssignApproversForm
    model = Project
    template_name = "application_projects/modals/assign_pafapprovers.html"

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, pk=self.kwargs["pk"])
        has_permission(
            "update_paf_assigned_approvers",
            request.user,
            self.project,
            raise_exception=True,
            request=request,
        )
        return super().dispatch(request, *args, **kwargs)

    def get(self, *args, **kwargs):
        from ..forms.project import get_latest_project_paf_approval_via_roles

        form = self.form_class(user=self.request.user, instance=self.project)
        paf_approval = get_latest_project_paf_approval_via_roles(
            project=self.project, roles=self.request.user.groups.all()
        )
        return render(
            self.request,
            self.template_name,
            context={
                "form": form,
                "value": _("Submit"),
                "pafapprover_exists": True if paf_approval.user else False,
                "object": self.project,
            },
        )

    def post(self, *args, **kwargs):
        from ..forms.project import get_latest_project_paf_approval_via_roles

        form = self.form_class(
            self.request.POST, user=self.request.user, instance=self.project
        )

        old_paf_approval = get_latest_project_paf_approval_via_roles(
            project=self.project, roles=self.request.user.groups.all()
        )

        if form.is_valid():
            form.save()

            # remove current task of user/user_group related to latest paf_approval of project
            if old_paf_approval.user:
                remove_tasks_for_user(
                    code=PAF_WAITING_APPROVAL,
                    user=old_paf_approval.user,
                    related_obj=self.project,
                )
            else:
                remove_tasks_for_user_group(
                    code=PAF_WAITING_ASSIGNEE,
                    user_group=old_paf_approval.paf_reviewer_role.user_roles.all(),
                    related_obj=self.project,
                )

            paf_approval = get_latest_project_paf_approval_via_roles(
                project=self.project, roles=self.request.user.groups.all()
            )

            if paf_approval.user:
                messenger(
                    MESSAGES.APPROVE_PAF,
                    request=self.request,
                    user=self.request.user,
                    source=self.project,
                    related=[paf_approval],
                )
                # add PAF waiting approval task to updated paf_approval user
                add_task_to_user(
                    code=PAF_WAITING_APPROVAL,
                    user=paf_approval.user,
                    related_obj=self.project,
                )
            else:
                messenger(
                    MESSAGES.ASSIGN_PAF_APPROVER,
                    request=self.request,
                    user=self.request.user,
                    source=self.project,
                )
                # add paf waiting for assignee task
                add_task_to_user_group(
                    code=PAF_WAITING_ASSIGNEE,
                    user_group=paf_approval.paf_reviewer_role.user_roles.all(),
                    related_obj=self.project,
                )

            return HttpResponseClientRefresh()

        return render(
            self.request,
            self.template_name,
            context={
                "form": form,
                "value": _("Submit"),
                "pafapprover_exists": True if old_paf_approval.user else False,
                "object": self.project,
            },
        )


class UpdatePAFApproversView(View):
    form_class = ApproversForm
    model = Project
    template_name = "application_projects/modals/update_pafapprovers.html"

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, pk=self.kwargs["pk"])
        has_permission(
            "paf_approvers_update",
            request.user,
            self.project,
            raise_exception=True,
            request=request,
        )
        return super().dispatch(request, *args, **kwargs)

    def get(self, *args, **kwargs):
        form = self.form_class(instance=self.project)
        project_settings = ProjectSettings.for_request(self.request)
        return render(
            self.request,
            self.template_name,
            context={
                "form": form,
                "value": _("Submit"),
                "project_settings": project_settings,
                "object": self.project,
            },
        )

    def post(self, *args, **kwargs):
        form = self.form_class(self.request.POST, instance=self.project)

        project_settings = ProjectSettings.for_request(self.request)
        if form.is_valid():
            old_approvers = None
            if self.project.paf_approvals.exists():
                old_approvers = list(
                    self.project.paf_approvals.filter(approved=False).values_list(
                        "user__id", flat=True
                    )
                )
            # remove PAF waiting assignee/approval task for paf approval user/reviewer roles.
            if project_settings.paf_approval_sequential:
                paf_approval = self.project.paf_approvals.filter(approved=False).first()
                if paf_approval.user:
                    remove_tasks_for_user(
                        code=PAF_WAITING_APPROVAL,
                        user=paf_approval.user,
                        related_obj=self.project,
                    )
                else:
                    remove_tasks_for_user_group(
                        code=PAF_WAITING_ASSIGNEE,
                        user_group=paf_approval.paf_reviewer_role.user_roles.all(),
                        related_obj=self.project,
                    )
            else:
                for approval in self.project.paf_approvals.filter(approved=False):
                    if approval.user:
                        remove_tasks_for_user(
                            code=PAF_WAITING_APPROVAL,
                            user=approval.user,
                            related_obj=self.project,
                        )
                    else:
                        remove_tasks_for_user_group(
                            code=PAF_WAITING_ASSIGNEE,
                            user_group=approval.paf_reviewer_role.user_roles.all(),
                            related_obj=self.project,
                        )

            form.save()

            paf_approvals = self.project.paf_approvals.filter(approved=False)

            if old_approvers and paf_approvals:
                # if approvers exists already
                if project_settings.paf_approval_sequential:
                    user = paf_approvals.first().user
                    if user and user.id != old_approvers[0]:
                        # notify only if first user/approver is updated
                        messenger(
                            MESSAGES.APPROVE_PAF,
                            request=self.request,
                            user=self.request.user,
                            source=self.project,
                            related=[paf_approvals.first()],
                        )
                        # add PAF waiting approval task to paf_approval user
                        add_task_to_user(
                            code=PAF_WAITING_APPROVAL,
                            user=user,
                            related_obj=self.project,
                        )
                    elif not user:
                        messenger(
                            MESSAGES.ASSIGN_PAF_APPROVER,
                            request=self.request,
                            user=self.request.user,
                            source=self.project,
                        )
                        # add PAF waiting assignee to paf_approvals reviewer roles
                        add_task_to_user_group(
                            code=PAF_WAITING_ASSIGNEE,
                            user_group=paf_approvals.first().paf_reviewer_role.user_roles.all(),
                            related_obj=self.project,
                        )
                else:
                    if paf_approvals.filter(user__isnull=False).exists():
                        messenger(
                            MESSAGES.APPROVE_PAF,
                            request=self.request,
                            user=self.request.user,
                            source=self.project,
                            related=paf_approvals.filter(user__isnull=False),
                        )
                        # add PAF waiting approval task for paf_approvals users
                        for paf_approval in paf_approvals.filter(user__isnull=False):
                            add_task_to_user(
                                code=PAF_WAITING_APPROVAL,
                                user=paf_approval.user,
                                related_obj=self.project,
                            )
                    if paf_approvals.filter(user__isnull=True).exists():
                        messenger(
                            MESSAGES.ASSIGN_PAF_APPROVER,
                            request=self.request,
                            user=self.request.user,
                            source=self.project,
                        )
                        # add PAF waiting assignee task for paf_approvals reviewer_roles
                        for paf_approval in paf_approvals.filter(user__isnull=True):
                            add_task_to_user_group(
                                code=PAF_WAITING_ASSIGNEE,
                                user_group=paf_approval.paf_reviewer_role.user_roles.all(),
                                related_obj=self.project,
                            )
            elif paf_approvals:
                # :todo: check if this is covering any case(might be a duplicate of SendForApprovalView)
                if paf_approvals.filter(user__isnull=False).exists():
                    messenger(
                        MESSAGES.APPROVE_PAF,
                        request=self.request,
                        user=self.request.user,
                        source=self.project,
                        related=paf_approvals.filter(user__isnull=False),
                    )
                    # add PAF waiting approval task for paf_approvals users
                    for paf_approval in paf_approvals.filter(user__isnull=False):
                        add_task_to_user(
                            code=PAF_WAITING_APPROVAL,
                            user=paf_approval.user,
                            related_obj=self.project,
                        )
                if paf_approvals.filter(user__isnull=True).exists():
                    messenger(
                        MESSAGES.ASSIGN_PAF_APPROVER,
                        request=self.request,
                        user=self.request.user,
                        source=self.project,
                    )
                    # add PAF waiting assignee task for paf_approvals reviewer_roles
                    for paf_approval in paf_approvals.filter(user__isnull=True):
                        add_task_to_user_group(
                            code=PAF_WAITING_ASSIGNEE,
                            user_group=paf_approval.paf_reviewer_role.user_roles.all(),
                            related_obj=self.project,
                        )

            messages.success(
                self.request, _("Project form approvers have been updated")
            )
            return HttpResponseClientRefresh()
        return render(
            self.request,
            self.template_name,
            context={
                "form": form,
                "value": _("Submit"),
                "project_settings": project_settings,
                "object": self.project,
            },
        )


@method_decorator(staff_or_finance_or_contracting_required, name="dispatch")
class ProjectDetailApprovalView(ProjectByIdMixin, DetailView):
    model = Project
    template_name_suffix = "_approval_detail"


@method_decorator(staff_or_finance_or_contracting_required, name="dispatch")
class ProjectDetailDownloadView(ProjectByIdMixin, SingleObjectMixin, View):
    model = Project

    def get(self, request, *args, **kwargs):
        export_type = kwargs.get("export_type", None)
        self.object = self.get_object()
        context = self.get_paf_download_context()
        template_path = "application_projects/paf_export.html"

        if export_type == "pdf":
            pdf_page_settings = PDFPageSettings.load(request_or_site=request)
            context["pagesize"] = pdf_page_settings.download_page_size
            context["show_footer"] = True
            return render_as_pdf(
                request=request,
                context=context,
                template_name=template_path,
                filename=self.get_slugified_file_name(export_type),
            )
        elif export_type == "docx":
            context["show_footer"] = False

            return self.render_as_docx(
                context=context,
                template=get_template(template_path),
                filename=self.get_slugified_file_name(export_type),
            )
        else:
            raise Http404(f"{export_type} type not supported at the moment")

    def render_as_docx(self, context, template, filename):
        html = template.render(context)

        buf = io.BytesIO()
        # Imported here to keep python-docx (and lxml) out of memory until needed.
        from docx import Document
        from htmldocx import HtmlToDocx

        document = Document()
        new_parser = HtmlToDocx()
        new_parser.add_html_to_document(html, document)
        document.save(buf)
        buf.seek(0)

        return FileResponse(
            buf, as_attachment=True, filename=filename, content_type="application/docx"
        )

    def get_slugified_file_name(self, export_type):
        return f"{datetime.date.today().strftime('%Y%m%d')}-{slugify(self.object.title)}.{export_type}"

    def get_paf_download_context(self):
        context = {}
        context["id"] = self.object.id
        context["title"] = self.object.title
        context["project_link"] = self.request.build_absolute_uri(
            self.object.get_absolute_url()
        )
        context["contractor_name"] = self.object.user

        context["approvals"] = self.object.paf_approvals.all()
        context["paf_data"] = self.get_paf_data_with_field(self.object)
        context["submission"] = self.object.submission
        context["submission_link"] = self.request.build_absolute_uri(
            reverse(
                "apply:submissions:detail", kwargs={"pk": self.object.submission_id}
            )
        )
        context["supporting_documents"] = self.get_supporting_documents(self.object)
        context["org_name"] = settings.ORG_LONG_NAME
        return context

    def get_paf_data_with_field(self, project):
        data_dict = {}
        form_data_dict = project.form_data
        for field in project.form_fields.raw_data:
            if field.get("type", None) in ["file", "multi_file"]:
                continue
            if field["id"] in form_data_dict.keys():
                if isinstance(field["value"], dict) and "field_label" in field["value"]:
                    data_dict[field["value"]["field_label"]] = form_data_dict[
                        field["id"]
                    ]

        return data_dict

    def get_supporting_documents(self, project):
        documents_dict = {}
        for packet_file in project.packet_files.all():
            documents_dict[packet_file.title] = self.request.build_absolute_uri(
                reverse(
                    "apply:projects:document",
                    kwargs={"pk": project.pk, "file_pk": packet_file.id},
                )
            )
        return documents_dict
