from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DetailView, UpdateView
from django.views.generic.detail import SingleObjectMixin
from django_filters.views import FilterView
from django_htmx.http import (
    HttpResponseClientRefresh,
)
from django_tables2 import SingleTableMixin

from hypha.apply.activity.messaging import MESSAGES, messenger
from hypha.apply.users.decorators import staff_or_finance_required, staff_required
from hypha.apply.utils.storage import PrivateMediaView

from ...stream_forms.models import BaseStreamForm
from ..filters import ReportingFilter, ReportListFilter
from ..forms import ReportEditForm, ReportFrequencyForm
from ..models import Project, Report, ReportConfig, ReportPrivateFiles
from ..permissions import has_permission
from ..tables import ReportingTable, ReportListTable
from ..utils import get_placeholder_file


class ReportingMixin:
    def dispatch(self, *args, **kwargs):
        project = self.get_object()
        if project.is_in_progress:
            if not hasattr(project, "report_config"):
                ReportConfig.objects.create(project=project)

        return super().dispatch(*args, **kwargs)


@method_decorator(login_required, name="dispatch")
class ReportAccessMixin(UserPassesTestMixin):
    model = Report

    def test_func(self):
        if self.request.user.is_apply_staff:
            return True

        if self.request.user.is_finance:
            return True

        if self.request.user == self.get_object().project.user:
            return True

        return False


@method_decorator(login_required, name="dispatch")
class ReportDetailView(DetailView):
    model = Report

    def dispatch(self, *args, **kwargs):
        report = self.get_object()
        permission, _ = has_permission(
            "report_view", self.request.user, object=report, raise_exception=True
        )
        return super().dispatch(*args, **kwargs)


@method_decorator(login_required, name="dispatch")
class ReportUpdateView(BaseStreamForm, UpdateView):
    model = Report
    # Values for `object`, `form_class`, and `form_fields` are set during `dispatch` and functions it calls.
    object = None
    form_class = None
    form_fields = None

    def get_form_class(self, draft=False, form_data=None, user=None):
        """
        Expects self.form_fields to have already been set.
        """
        # This is where the magic happens.
        fields = self.get_form_fields(draft, form_data, user)
        the_class = type(
            "WagtailStreamForm",
            (ReportEditForm,),
            fields,
        )
        return the_class

    def dispatch(self, request, *args, **kwargs):
        report = self.get_object()
        permission, _ = has_permission(
            "report_update", self.request.user, object=report, raise_exception=True
        )
        self.object = report
        # super().dispatch calls get_context_data() which calls the rest to get the form fully ready for use.
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        """
        Django note: super().dispatch calls get_context_data.
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

    def get_form(self, form_class=None):
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
            form_class = self.get_form_class()
        report_instance = form_class(**self.get_form_kwargs())
        return report_instance

    def get_initial(self):
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

    def get_form_kwargs(self):
        form_kwargs = {
            "user": self.request.user,
            **super().get_form_kwargs(),
        }
        return form_kwargs

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            form.save(form_fields=self.form_fields)
            form.delete_temporary_files()
            response = HttpResponseRedirect(self.get_success_url())
        else:
            response = self.form_invalid(form)
        return response

    def get_success_url(self):
        success_url = self.object.project.get_absolute_url()
        return success_url

    def form_valid(self, form):
        response = super().form_valid(form)

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

        # Required for django-file-form: delete temporary files for the new files
        # that are uploaded.
        form.delete_temporary_files()
        return response


class ReportPrivateMedia(ReportAccessMixin, PrivateMediaView):
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
    model = Report

    def post(self, *args, **kwargs):
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
    form_class = ReportFrequencyForm
    model = ReportConfig
    template_name = "application_projects/modals/report_frequency_config.html"

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, id=kwargs.get("pk"))
        self.object = self.project.report_config
        return super().dispatch(request, *args, **kwargs)

    def get_due_report_data(self):
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
        form = self.get_form(self.request.POST)
        if form.is_valid():
            if "disable-reporting" in self.request.POST:
                form.instance.disable_reporting = True
                form.instance.schedule_start = None
                form.save()
                messenger(
                    MESSAGES.DISABLED_REPORTING,
                    request=self.request,
                    user=self.request.user,
                    source=self.project,
                )
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
    queryset = Report.objects.submitted().for_table()
    filterset_class = ReportListFilter
    table_class = ReportListTable
    template_name = "application_projects/report_list.html"


@method_decorator(staff_or_finance_required, name="dispatch")
class ReportingView(SingleTableMixin, FilterView):
    queryset = Project.objects.for_reporting_table()
    filterset_class = ReportingFilter
    table_class = ReportingTable
    template_name = "application_projects/reporting.html"
