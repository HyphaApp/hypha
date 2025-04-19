"""
Module for handling project reporting functionality in the Hypha application.

This module provides views and utilities for managing project reports, including
creating, viewing, updating, and administering reports. It implements access control,
form handling, and notification systems for the reporting workflow.

Dependencies:
- Django (including django-filters, django-htmx, django-tables2)
- Hypha application modules (activity, projects, stream_forms, users, utils)
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import DetailView, UpdateView
from django.views.generic.detail import SingleObjectMixin
from django_filters.views import FilterView
from django_htmx.http import HttpResponseClientRefresh
from django_tables2 import SingleTableMixin
from rolepermissions.checkers import has_object_permission

from hypha.apply.activity.messaging import MESSAGES, messenger
from hypha.apply.projects.models import Project
from hypha.apply.projects.utils import get_placeholder_file
from hypha.apply.stream_forms.models import BaseStreamForm
from hypha.apply.users.decorators import staff_or_finance_required, staff_required
from hypha.apply.utils.storage import PrivateMediaView

from .filters import ReportingFilter, ReportListFilter
from .forms import ReportEditForm, ReportFrequencyForm
from .models import Report, ReportConfig, ReportPrivateFiles
from .tables import ReportingTable, ReportListTable


class ReportingMixin:
    """
    Mixin that ensures a project has a report configuration.

    If a project is in progress but doesn't have a report_config,
    this mixin creates one before proceeding with the view.
    """

    def dispatch(self, *args, **kwargs):
        """
        Ensure project has a report configuration if it's in progress.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            HttpResponse: The response from the parent class's dispatch method.
        """
        project = self.get_object()
        if project.is_in_progress:
            if not hasattr(project, "report_config"):
                ReportConfig.objects.create(project=project)

        return super().dispatch(*args, **kwargs)


@method_decorator(login_required, name="dispatch")
class ReportAccessMixin(UserPassesTestMixin):
    """
    Mixin that controls access to report-related views.

    Allows access to staff members, finance users, and the project owner.
    """

    model = Report
    permission_denied_message = _("You do not have permission to access this report.")

    def test_func(self) -> bool:
        """
        Test whether the current user has access to the report.

        Returns:
            bool | None: True if user has permission to view the report, False otherwise.
        """
        return has_object_permission(
            "view_report", self.request.user, self.get_object()
        )


@method_decorator(login_required, name="dispatch")
class ReportDetailView(DetailView):
    """
    View for displaying the details of a report.
    """

    model = Report
    template_name = "reports/report_detail.html"
    permission_denied_message = _("You do not have permission to access this report.")

    def dispatch(self, *args, **kwargs):
        report = self.get_object()
        if not has_object_permission("view_report", self.request.user, report):
            raise PermissionDenied(self.permission_denied_message)
        return super().dispatch(*args, **kwargs)


@method_decorator(login_required, name="dispatch")
class ReportUpdateView(BaseStreamForm, UpdateView):
    """
    View for updating a report.

    This view handles both creating new reports and editing existing ones.
    It supports draft saving and manages form field population from existing data.
    """

    model = Report
    # Values for `object`, `form_class`, and `form_fields` are set during `dispatch` and functions it calls.
    object = None
    form_class = None
    form_fields = None
    submission_form_class = ReportEditForm
    template_name = "reports/report_form.html"
    permission_denied_message = _("You do not have permission to update this report.")

    def dispatch(self, request, *args, **kwargs):
        """
        Set up the report object and check permissions before proceeding.

        Args:
            request: The HttpRequest object.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            HttpResponse: The response from the parent class's dispatch method.

        Raises:
            PermissionDenied: If user doesn't have 'report_update' permission.
        """
        report = self.get_object()
        self.object = report
        if not has_object_permission("update_report", self.request.user, report):
            raise PermissionDenied(self.permission_denied_message)
        # super().dispatch calls get_context_data() which calls the rest to get the form fully ready for use.
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        """
        Prepare the context data for the template.

        Django note: super().dispatch calls get_context_data.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            dict: The context data dictionary.
        """
        # Is this where we need to get the associated form fields? Not in the form itself but up here? Yes. But in a
        # roundabout way: get_form (here) gets fields and calls get_form_class (here) which calls get_form_fields
        # (super) which sets up the fields in the returned form.
        form = self.get_form()
        context_data = {
            "form": form,
            "object": self.object,
            "report_form": True
            if self.object.project.submission.page.specific.report_forms.first()
            else False,
            **kwargs,
        }
        return context_data

    def get_form(self, form_class=None, draft=False):
        """
        Return an instance of the form to be used in this view.

        Handles setting up form fields based on the report configuration or previous data.

        Args:
            form_class: The form class to use, if not using the default.
            draft: Boolean indicating if this is a draft form.

        Returns:
            Form: An instance of the form to be used.
        """
        if self.object.current is None or self.object.form_fields is None:
            # Here is where we get the form_fields, the ProjectReportForm associated with the Fund:
            report_form = (
                self.object.project.submission.page.specific.report_forms.first()
            )
            if report_form:
                self.form_fields = report_form.form.form_fields
            else:
                self.form_fields = {}
        else:
            self.form_fields = self.object.form_fields

        if form_class is None:
            form_class = self.get_form_class(draft=draft)
        report_instance = form_class(**self.get_form_kwargs())
        return report_instance

    def get_initial(self):
        """
        Get initial data for the form.

        Populates the form with existing data from draft or current report version.
        Handles file fields specially to properly display them.

        Returns:
            dict: Initial data for the form.
        """
        initial = {}
        if self.object.draft:
            current = self.object.draft
        else:
            current = self.object.current

        # current here is a ReportVersion which should already have the data associated.
        if current:
            # The following allows existing data to populate the form. This code was inspired by (aka copied from)
            # ProjectFormEditView.get_paf_form_kwargs().
            initial = current.raw_data
            # Is the following needed to see the file in a friendly URL? Does not appear so. But needed to not blow up.
            for field_id in current.file_field_ids:
                initial.pop(field_id + "-uploads", False)
                initial[field_id] = get_placeholder_file(current.raw_data.get(field_id))

        return initial

    def get_form_kwargs(self) -> dict:
        """
        Get the keyword arguments for instantiating the form.

        Adds the current user to the form kwargs.

        Returns:
            dict: The keyword arguments for the form.
        """
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables and then check if it's valid.

        Handles saving drafts, form validation, and sending notifications.

        Args:
            request: The HttpRequest object.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            HttpResponse: Redirect to success URL or redisplay form if invalid.
        """
        save_draft = "save" in request.POST  # clicked on save button?
        form = self.get_form(draft=save_draft)
        if form.is_valid():
            form.save(form_fields=self.form_fields)
            form.delete_temporary_files()

            should_notify = True
            if self.object.draft:
                # It was a draft submission
                should_notify = False
            else:
                if self.object.submitted != self.object.current.submitted:
                    # It was a staff edit - post submission
                    should_notify = False

            if should_notify:
                messenger(
                    MESSAGES.SUBMIT_REPORT,
                    request=self.request,
                    user=self.request.user,
                    source=self.object.project,
                    related=self.object,
                )
            response = HttpResponseRedirect(self.get_success_url())
        else:
            response = self.form_invalid(form)
        return response

    def get_success_url(self) -> str:
        return self.object.project.get_absolute_url()


class ReportPrivateMedia(ReportAccessMixin, PrivateMediaView):
    """
    View for handling private media files attached to reports.

    Ensures proper access control and redirects users to the latest report version
    if they try to access an outdated document.
    """

    def dispatch(self, *args, **kwargs):
        report_pk = self.kwargs["pk"]
        self.report = get_object_or_404(Report, pk=report_pk)
        file_pk = kwargs.get("file_pk")
        self.document = get_object_or_404(
            ReportPrivateFiles.objects, report__report=self.report, pk=file_pk
        )

        if not hasattr(self.document.report, "live_for_report"):
            # this is not a document in the live report
            # send the user to the report page to see latest version
            return redirect(self.report.get_absolute_url())

        return super().dispatch(*args, **kwargs)

    def get_media(self, *args, **kwargs):
        return self.document.document


@method_decorator(staff_required, name="dispatch")
class ReportSkipView(SingleObjectMixin, View):
    """
    View for marking a report as skipped.

    Only staff can skip reports, and only unsubmitted reports that aren't
    the current due report can be skipped.
    """

    model = Report

    def post(self, *args, **kwargs):
        """
        Handle POST requests to toggle the skipped status of a report.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            HttpResponseClientRefresh: A response that refreshes the client.
        """
        report = self.get_object()
        unsubmitted = not report.current
        not_current = report.project.report_config.current_due_report() != report
        if unsubmitted and not_current:
            report.skipped = not report.skipped
            report.save()
            messenger(
                MESSAGES.SKIPPED_REPORT,
                request=self.request,
                user=self.request.user,
                source=report.project,
                related=report,
            )
        return HttpResponseClientRefresh()


@method_decorator(staff_required, name="dispatch")
class ReportFrequencyUpdate(View):
    """
    View for updating the reporting frequency configuration for a project.

    Allows staff to set when reports are due and to enable/disable reporting
    for a project.
    """

    form_class = ReportFrequencyForm
    model = ReportConfig
    template_name = "reports/modals/report_frequency_config.html"
    permission_denied_message = _(
        "You do not have permission to update reporting configurations."
    )

    def dispatch(self, request, *args, **kwargs):
        """
        Set up the project and report configuration objects.

        Args:
            request: The HttpRequest object.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            HttpResponse: The response from the parent class's dispatch method.
        """
        self.project = get_object_or_404(Project, submission__id=kwargs.get("pk"))
        if not has_object_permission(
            "update_report_config", self.request.user, self.project
        ):
            raise PermissionDenied(self.permission_denied_message)
        self.object = self.project.report_config
        return super().dispatch(request, *args, **kwargs)

    def get_due_report_data(self):
        """
        Get data about the current due report for the project.

        Returns:
            dict: Data containing start date and project end date if reporting is enabled,
                  empty dict otherwise.
        """
        report_data = {}
        if not self.object.disable_reporting:
            project_end_date = self.project.end_date
            if self.object.current_due_report():
                start_date = self.object.current_due_report().start_date
            else:
                start_date = self.object.last_report().start_date
            report_data = {"startDate": start_date, "projectEndDate": project_end_date}
        return report_data

    def get(self, *args, **kwargs):
        """
        Handle GET requests to display the form.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            HttpResponse: Rendered template with form and context data.
        """
        form = self.get_form()
        report_data = self.get_due_report_data()

        return render(
            self.request,
            self.template_name,
            context={
                "form": form,
                "object": self.object,
                "report_data": report_data,
            },
        )

    def get_form_kwargs(self, **kwargs):
        """
        Get the keyword arguments for instantiating the form.

        Sets initial start date based on current reporting configuration.

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            dict: The keyword arguments for the form.
        """
        kwargs = kwargs or {}
        kwargs["instance"] = self.object
        if not self.object.disable_reporting:
            # Current due report can be none for ONE_TIME(does not repeat),
            # In case of ONE_TIME, either reporting is already completed(last_report exists)
            # or there should be a current_due_report.
            if self.object.current_due_report():
                kwargs["initial"] = {
                    "start": self.object.current_due_report().end_date,
                }
            else:
                kwargs["initial"] = {
                    "start": self.object.last_report().end_date,
                }
        else:
            kwargs["initial"] = {
                "start": self.project.start_date,
            }
        return kwargs

    def get_form(self, *args, **kwargs):
        if self.project.is_in_progress:
            return self.form_class(*args, **(self.get_form_kwargs(**kwargs)))
        return None

    def post(self, *args, **kwargs):
        """
        Handle POST requests to update reporting configuration.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            HttpResponse: Client refresh response or form with errors.
        """
        form = self.get_form(self.request.POST)
        if form.is_valid():
            if "disable-reporting" in self.request.POST:
                form.instance.disable_reporting = True
                form.instance.schedule_start = None
                form.save()
                messages.success(self.request, _("Reporting disabled"))
            else:
                form.instance.disable_reporting = False
                form.instance.schedule_start = form.cleaned_data["start"]
                form.save()
                messenger(
                    MESSAGES.REPORT_FREQUENCY_CHANGED,
                    request=self.request,
                    user=self.request.user,
                    source=self.project,
                    related=self.object,
                )
            return HttpResponseClientRefresh()

        report_data = self.get_due_report_data()
        return render(
            self.request,
            self.template_name,
            context={
                "form": form,
                "object": self.object,
                "report_data": report_data,
            },
        )


@method_decorator(staff_or_finance_required, name="dispatch")
class ReportListView(SingleTableMixin, FilterView):
    """
    View for displaying a table of submitted reports.

    Only accessible to staff and finance users.
    """

    queryset = Report.objects.submitted().for_table()
    filterset_class = ReportListFilter
    table_class = ReportListTable
    template_name = "reports/report_list.html"


@method_decorator(staff_or_finance_required, name="dispatch")
class ReportingView(SingleTableMixin, FilterView):
    """
    View for displaying a table of projects with reporting information.

    Only accessible to staff and finance users.
    """

    queryset = Project.objects.for_reporting_table()
    filterset_class = ReportingFilter
    table_class = ReportingTable
    template_name = "reports/reporting.html"
