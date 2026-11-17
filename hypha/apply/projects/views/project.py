import copy
import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import (
    DetailView,
)
from django_filters.views import FilterView
from django_htmx.http import (
    HttpResponseClientRefresh,
)
from django_tables2 import SingleTableMixin

from hypha.apply.activity.messaging import MESSAGES, messenger
from hypha.apply.activity.models import ALL, COMMENT, Activity
from hypha.apply.activity.views import ActivityContextMixin
from hypha.apply.funds.models import ApplicationSubmission
from hypha.apply.todo.utils import get_project_lead_tasks
from hypha.apply.users.decorators import (
    staff_or_finance_or_contracting_required,
    staff_required,
)
from hypha.apply.utils.views import DelegateableView, ViewDispatcher

from ..filters import ProjectListFilter
from ..forms import (
    ChangeProjectStatusForm,
    UpdateProjectContractNumberForm,
    UpdateProjectDatesForm,
    UpdateProjectLeadForm,
    UpdateProjectTitleForm,
)
from ..models.project import (
    PROJECT_PUBLIC_STATUSES,
    ContractDocumentCategory,
    DocumentCategory,
    PAFApprovals,
    Project,
    ProjectSettings,
)
from ..permissions import has_permission
from ..reports.views import ReportingMixin
from ..tables import ProjectsListTable
from ..utils import (
    get_project_status_choices,
)
from .mixins import ContractsMixin, ProjectByIdMixin


@method_decorator(staff_required, name="dispatch")
class UpdateLeadView(ProjectByIdMixin, View):
    model = Project
    form_class = UpdateProjectLeadForm
    template_name = "application_projects/modals/lead_update.html"

    def dispatch(self, request, *args, **kwargs):
        self.project = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def get(self, *args, **kwargs):
        form = self.form_class(instance=self.project)
        return render(
            self.request,
            self.template_name,
            context={
                "form": form,
                "value": _("Update"),
                "object": self.project,
            },
        )

    def post(self, *args, **kwargs):
        # Fetch the old lead from the database
        old_lead = copy.copy(self.project.lead)
        form = self.form_class(self.request.POST, instance=self.project)
        if form.is_valid():
            tasks = get_project_lead_tasks(self.project.lead, self.project)

            form.save()
            tasks.update(user=self.project.lead)

            messenger(
                MESSAGES.UPDATE_PROJECT_LEAD,
                request=self.request,
                user=self.request.user,
                source=self.project,
                related=old_lead or _("Unassigned"),
            )

            return HttpResponse(
                status=204,
                headers={
                    "HX-Trigger": json.dumps(
                        {
                            "leadUpdated": None,
                            "showMessage": _("Lead has been updated."),
                        }
                    ),
                },
            )
        return render(
            self.request,
            self.template_name,
            context={
                "form": form,
                "value": _("Update"),
                "object": self.project,
            },
        )


@login_required
def update_project_title(request, pk):
    if not request.user.is_apply_staff:
        raise PermissionDenied

    project = get_object_or_404(Project, pk=pk)
    template_name = "application_projects/modals/project_title_update.html"

    form = UpdateProjectTitleForm(instance=project)

    if request.method == "POST":
        old_title = copy.copy(project.title)
        form = UpdateProjectTitleForm(request.POST, instance=project)

        if form.is_valid():
            form.save()
            messenger(
                MESSAGES.UPDATE_PROJECT_TITLE,
                request=request,
                user=request.user,
                source=project,
                related=old_title,
            )

            return HttpResponse(
                status=204,
                headers={
                    "HX-Trigger": json.dumps(
                        {
                            "titleUpdated": None,
                            "showMessage": _("Title has been updated"),
                        }
                    ),
                },
            )

    ctx = {
        "form": form,
        "value": _("Update"),
        "object": project,
    }
    return render(request, template_name, ctx)


@login_required
def update_project_dates(request, pk):
    if not request.user.is_apply_staff:
        raise PermissionDenied

    project = get_object_or_404(Project, pk=pk)
    template_name = "application_projects/modals/project_dates_update.html"

    form = UpdateProjectDatesForm(instance=project)

    if request.method == "POST":
        form = UpdateProjectDatesForm(request.POST, instance=project)

        if form.is_valid():
            form.save()

            return HttpResponse(
                status=204,
                headers={
                    "HX-Trigger": json.dumps(
                        {
                            "informationUpdated": None,
                            "showMessage": _("Dates has been updated"),
                        }
                    ),
                },
            )

    ctx = {
        "form": form,
        "value": _("Update"),
        "object": project,
    }
    return render(request, template_name, ctx)


@login_required
def update_project_contract_number(request, pk):
    if not (request.user.is_org_faculty):
        raise PermissionDenied

    project = get_object_or_404(Project, submission__id=pk)
    template_name = "application_projects/modals/project_contract_number_update.html"

    form = UpdateProjectContractNumberForm(instance=project)

    if request.method == "POST":
        form = UpdateProjectContractNumberForm(request.POST, instance=project)

        if form.is_valid():
            form.save()
            messenger(
                MESSAGES.UPDATE_PROJECT_CONTRACT_NUMBER,
                request=request,
                user=request.user,
                source=project,
            )

            return HttpResponse(
                status=204,
                headers={
                    "HX-Trigger": json.dumps(
                        {
                            "informationUpdated": None,
                            "showMessage": _("Contract number has been updated"),
                        }
                    ),
                },
            )

    ctx = {
        "form": form,
        "value": _("Update"),
        "object": project,
    }
    return render(request, template_name, ctx)


# CONTRACTS


class ChangeProjectstatusView(View):
    """
    Project status can be updated manually only in 'IN PROGRESS, CLOSING and COMPLETE' state.
    """

    form_class = ChangeProjectStatusForm
    model = Project
    template_name = "application_projects/modals/project_status_update.html"

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, pk=self.kwargs["pk"])
        has_permission(
            "project_status_update", request.user, self.project, raise_exception=True
        )
        return super().dispatch(request, *args, **kwargs)

    def get(self, *args, **kwargs):
        form = self.form_class(instance=self.project)
        return render(
            self.request,
            self.template_name,
            context={
                "form": form,
                "value": _("Update"),
                "object": self.project,
            },
        )

    def post(self, *args, **kwargs):
        old_stage = self.project.status
        form = self.form_class(self.request.POST, instance=self.project)

        if form.is_valid():
            form.save()

            comment = form.cleaned_data.get("comment", "")

            if comment:
                Activity.objects.create(
                    user=self.request.user,
                    type=COMMENT,
                    source=self.project,
                    timestamp=timezone.now(),
                    message=comment,
                    visibility=ALL,
                )

            messenger(
                MESSAGES.PROJECT_TRANSITION,
                request=self.request,
                user=self.request.user,
                source=self.project,
                related=old_stage,
            )

            messages.success(self.request, _("Project status has been updated"))
            return HttpResponseClientRefresh()
        return render(
            self.request,
            self.template_name,
            context={
                "form": form,
                "value": _("Update"),
                "object": self.project,
            },
        )


class BaseProjectDetailView(ReportingMixin, ProjectByIdMixin, DetailView):
    def get_object(self, queryset=None):
        if not hasattr(self, "_object_cache"):
            self._object_cache = super().get_object()
        return self._object_cache

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["statuses"] = get_project_status_choices()
        context["current_status_index"] = [
            status for status, _ in get_project_status_choices()
        ].index(self.object.status)
        context["supporting_documents_configured"] = (
            True if DocumentCategory.objects.count() else False
        )
        context["contracting_documents_configured"] = (
            True if ContractDocumentCategory.objects.count() else False
        )
        if hasattr(self.object, "report_config"):
            self.object.report_config.ensure_due_report()
        return context


class AdminProjectDetailView(
    ActivityContextMixin,
    DelegateableView,
    ContractsMixin,
    BaseProjectDetailView,
):
    model = Project
    template_name_suffix = "_admin_detail"
    form_views: list = []

    def dispatch(self, *args, **kwargs):
        project = self.get_object()
        has_permission(
            "project_access", self.request.user, object=project, raise_exception=True
        )
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["statuses"] = get_project_status_choices()
        context["current_status_index"] = [
            status for status, _ in get_project_status_choices()
        ].index(self.object.status)
        project_settings = ProjectSettings.for_request(self.request)
        context["project_settings"] = project_settings
        context["paf_approvals"] = PAFApprovals.objects.filter(project=self.object)
        return context


class ApplicantProjectDetailView(
    ActivityContextMixin,
    DelegateableView,
    ContractsMixin,
    BaseProjectDetailView,
):
    model = Project
    template_name_suffix = "_detail"
    form_views: list = []

    def dispatch(self, request, *args, **kwargs):
        project = self.get_object()
        has_permission(
            "project_access", request.user, object=project, raise_exception=True
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["statuses"] = PROJECT_PUBLIC_STATUSES
        context["current_status_index"] = [
            status for status, _ in PROJECT_PUBLIC_STATUSES
        ].index(self.object.status)
        context["remaining_contract_document_categories"] = (
            ContractDocumentCategory.objects.filter(
                ~Q(contract_packet_files__project=self.object)
            )
        )
        return context


class ProjectDetailView(ViewDispatcher):
    admin_view = AdminProjectDetailView
    finance_view = AdminProjectDetailView
    contracting_view = AdminProjectDetailView
    applicant_view = ApplicantProjectDetailView


@login_required
def project_detail_redirect(request, pk):
    """Redirect the legacy /projects/<pk>/ path to the submission-nested URL."""
    project = get_object_or_404(Project, pk=pk)
    return HttpResponseRedirect(project.get_absolute_url())


@method_decorator(login_required, name="dispatch")
class SubmissionProjectsView(View):
    """Landing page for a submission's projects.

    A submission can have several projects (one per funding "bucket").
    Redirect straight to the project when only one is accessible, otherwise
    list them so the user can pick.
    """

    def dispatch(self, request, pk, *args, **kwargs):
        submission = get_object_or_404(ApplicationSubmission, pk=pk)
        projects = [
            project
            for project in submission.projects.all()
            if has_permission(
                "project_access",
                request.user,
                object=project,
                raise_exception=False,
            )[0]
        ]
        if not projects:
            raise Http404(_("No projects for this submission"))
        if len(projects) == 1:
            return HttpResponseRedirect(projects[0].get_absolute_url())
        return render(
            request,
            "application_projects/submission_projects.html",
            {"submission": submission, "projects": projects},
        )


@method_decorator(staff_or_finance_or_contracting_required, name="dispatch")
class ProjectListView(SingleTableMixin, FilterView):
    filterset_class = ProjectListFilter
    queryset = Project.objects.for_table()
    table_class = ProjectsListTable
    template_name = "application_projects/project_list.html"

    excluded_fields = settings.PROJECTS_TABLE_EXCLUDED_FIELDS

    def get_filterset_kwargs(self, filterset_class, **kwargs):
        new_kwargs = super().get_filterset_kwargs(filterset_class)
        new_kwargs["exclude"] = self.excluded_fields
        new_kwargs.update(kwargs)
        return new_kwargs

    def get_table_kwargs(self):
        return {"exclude": self.excluded_fields}
