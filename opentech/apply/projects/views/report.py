from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db.models import F
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import (
    DetailView,
    UpdateView,
)
from django.views.generic.detail import SingleObjectMixin

from opentech.apply.activity.messaging import MESSAGES, messenger
from opentech.apply.utils.storage import PrivateMediaView
from opentech.apply.users.decorators import staff_required

from ..models import Report, ReportConfig, ReportPrivateFiles
from ..forms import ReportEditForm


class ReportingMixin:
    def dispatch(self, *args, **kwargs):
        project = self.get_object()
        if project.is_in_progress:
            if not hasattr(project, 'report_config'):
                ReportConfig.objects.create(project=project)

        return super().dispatch(*args, **kwargs)


class ReportAccessMixin:
    def dispatch(self, request, *args, **kwargs):
        is_admin = request.user.is_apply_staff
        is_owner = request.user == self.get_object().project.user
        if not (is_owner or is_admin):
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)


@method_decorator(login_required, name='dispatch')
class ReportDetailView(ReportAccessMixin, DetailView):
    model = Report

    def dispatch(self, *args, **kwargs):
        report = self.get_object()
        if not report.current and not report.skipped:
            raise Http404
        return super().dispatch(*args, **kwargs)


@method_decorator(login_required, name='dispatch')
class ReportUpdateView(ReportAccessMixin, UpdateView):
    form_class = ReportEditForm
    model = Report

    def dispatch(self, *args, **kwargs):
        report = self.get_object()
        if not report.can_submit:
            raise Http404
        if report.current and self.request.user.is_applicant:
            raise Http404
        return super().dispatch(*args, **kwargs)

    def get_initial(self):
        if self.object.draft:
            current = self.object.draft
        else:
            current = self.object.current

        if current:
            return {
                'content': current.content,
                'file_list': current.files.all(),
            }

        return {}

    def get_form_kwargs(self):
        return {
            'user': self.request.user,
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

        return response


@method_decorator(login_required, name='dispatch')
class ReportPrivateMedia(UserPassesTestMixin, PrivateMediaView):
    raise_exception = True

    def dispatch(self, *args, **kwargs):
        report_pk = self.kwargs['pk']
        self.report = get_object_or_404(Report, pk=report_pk)
        file_pk = kwargs.get('file_pk')
        self.document = get_object_or_404(
            ReportPrivateFiles.objects,
            report__report=self.report,
            pk=file_pk
        )

        if not hasattr(self.document.report, 'live_for_report'):
            # this is not a document in the live report
            # send the user to the report page to see latest version
            return redirect(self.report.get_absolute_url())

        return super().dispatch(*args, **kwargs)

    def get_media(self, *args, **kwargs):
        return self.document.document

    def test_func(self):
        if self.request.user.is_apply_staff:
            return True

        if self.request.user == self.report.project.user:
            return True

        return False


@method_decorator(staff_required, name='dispatch')
class ReportSkipView(SingleObjectMixin, View):
    model = Report

    def post(self, *args, **kwargs):
        report = self.get_object()
        if not report.current:
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
