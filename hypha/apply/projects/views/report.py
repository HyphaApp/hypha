from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DetailView, UpdateView
from django.views.generic.detail import SingleObjectMixin
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin

from hypha.apply.activity.messaging import MESSAGES, messenger
from hypha.apply.users.decorators import staff_or_finance_required, staff_required
from hypha.apply.utils.storage import PrivateMediaView
from hypha.apply.utils.views import DelegatedViewMixin, ViewDispatcher

from ..filters import ReportListFilter
from ..forms import ReportEditForm, ReportFrequencyForm
from ..models import Report, ReportConfig, ReportPrivateFiles
from ..permissions import has_permission
from ..tables import ReportListTable


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
class ReportUpdateView(UpdateView):
    form_class = ReportEditForm
    model = Report

    def dispatch(self, *args, **kwargs):
        report = self.get_object()
        permission, _ = has_permission(
            "report_update", self.request.user, object=report, raise_exception=True
        )
        return super().dispatch(*args, **kwargs)

    def get_initial(self):
        if self.object.draft:
            current = self.object.draft
        else:
            current = self.object.current

        if current:
            return {
                "public_content": current.public_content,
                "private_content": current.private_content,
                "file_list": current.files.all(),
            }

        return {}

    def get_form_kwargs(self):
        return {
            "user": self.request.user,
            **super().get_form_kwargs(),
        }

    def get_success_url(self):
        return self.object.project.get_absolute_url()

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
        return redirect(report.project.get_absolute_url())


@method_decorator(staff_required, name="dispatch")
class ReportFrequencyUpdate(DelegatedViewMixin, UpdateView):
    form_class = ReportFrequencyForm
    context_name = "update_frequency_form"
    model = ReportConfig

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.pop("user")
        project = kwargs["instance"]
        instance = project.report_config
        kwargs["instance"] = instance
        if not instance.disable_reporting:
            # Current due report can be none for ONE_TIME(does not repeat),
            # In case of ONE_TIME, either reporting is already completed(last_report exists)
            # or there should be a current_due_report.
            if instance.current_due_report():
                kwargs["initial"] = {
                    "start": instance.current_due_report().end_date,
                }
            else:
                kwargs["initial"] = {
                    "start": instance.last_report().end_date,
                }
        else:
            kwargs["initial"] = {
                "start": project.start_date,
            }
        return kwargs

    def get_object(self):
        project = self.get_parent_object()
        return project.report_config

    def get_form(self):
        if self.get_parent_object().is_in_progress:
            return super().get_form()
        return None

    def form_valid(self, form):
        config = form.instance
        # 'form-submitted-' is set as form_prefix in DelegateBase view
        if "disable-reporting" in self.request.POST.get(
            f"form-submitted-{self.context_name}"
        ):
            form.instance.disable_reporting = True
            form.instance.schedule_start = None
            response = super().form_valid(form)
            messenger(
                MESSAGES.DISABLED_REPORTING,
                request=self.request,
                user=self.request.user,
                source=config.project,
            )
        else:
            form.instance.disable_reporting = False
            form.instance.schedule_start = form.cleaned_data["start"]
            response = super().form_valid(form)
            messenger(
                MESSAGES.REPORT_FREQUENCY_CHANGED,
                request=self.request,
                user=self.request.user,
                source=config.project,
                related=config,
            )

        return response


@method_decorator(staff_or_finance_required, name="dispatch")
class ReportListAdminView(SingleTableMixin, FilterView):
    queryset = Report.objects.submitted().for_table()
    filterset_class = ReportListFilter
    table_class = ReportListTable
    template_name = "application_projects/report_list.html"


@method_decorator(login_required, name="dispatch")
class ReportListApplicantView(SingleTableMixin, FilterView):
    filterset_class = ReportListFilter
    table_class = ReportListTable
    template_name = "application_projects/report_list.html"

    def get_queryset(self):
        return (
            Report.objects.filter(project__user=self.request.user)
            .submitted()
            .for_table()
        )


@method_decorator(login_required, name="dispatch")
class ReportListView(ViewDispatcher):
    admin_view = ReportListAdminView
    finance_view = ReportListAdminView
    applicant_view = ReportListApplicantView
