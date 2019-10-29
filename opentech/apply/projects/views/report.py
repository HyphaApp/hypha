from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.utils.decorators import method_decorator
from django.core.exceptions import PermissionDenied
from django.views.generic import (
    UpdateView
)

from opentech.apply.utils.storage import PrivateMediaView

from ..models import Report, ReportConfig
from ..forms import ReportEditForm


class ReportingMixin:
    def dispatch(self, *args, **kwargs):
        project = self.get_object()
        if project.is_in_progress:
            if not hasattr(project, 'report_config'):
                ReportConfig.objects.create(project=project)

        return super().dispatch(*args, **kwargs)


class ReportAccessMixin:
    model = Report

    def dispatch(self, request, *args, **kwargs):
        is_admin = request.user.is_apply_staff
        is_owner = request.user == self.get_object().project.user
        if not (is_owner or is_admin):
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)


@method_decorator(login_required, name='dispatch')
class ReportUpdateView(ReportAccessMixin, UpdateView):
    form_class = ReportEditForm

    def get_success_url(self):
        return self.object.project.get_absolute_url()


@method_decorator(login_required, name='dispatch')
class ReportPrivateMedia(UserPassesTestMixin, PrivateMediaView):
    raise_exception = True

    def dispatch(self, *args, **kwargs):
        payment_pk = self.kwargs['pk']
        self.payment_request = get_object_or_404(PaymentRequest, pk=payment_pk)

        return super().dispatch(*args, **kwargs)

    def get_media(self, *args, **kwargs):
        file_pk = kwargs.get('file_pk')
        if not file_pk:
            return self.payment_request.invoice

        receipt = get_object_or_404(self.payment_request.receipts, pk=file_pk)
        return receipt.file

    def test_func(self):
        if self.request.user.is_apply_staff:
            return True

        if self.request.user == self.payment_request.project.user:
            return True

        return False
