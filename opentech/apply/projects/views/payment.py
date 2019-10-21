from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    UpdateView
)
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin

from opentech.apply.activity.messaging import MESSAGES, messenger
from opentech.apply.users.decorators import staff_required
from opentech.apply.utils.storage import PrivateMediaView
from opentech.apply.utils.views import (
    DelegateableView,
    DelegatedViewMixin,
    ViewDispatcher,
)

from ..forms import (
    ChangePaymentRequestStatusForm,
    CreatePaymentRequestForm,
    EditPaymentRequestForm,
)
from ..filters import PaymentRequestListFilter
from ..models import (
    PaymentRequest,
    Project
)
from ..tables import PaymentRequestsListTable


@method_decorator(login_required, name='dispatch')
class PaymentRequestAccessMixin:
    model = PaymentRequest

    def dispatch(self, request, *args, **kwargs):
        is_admin = request.user.is_apply_staff
        is_owner = request.user == self.get_object().project.user
        if not (is_owner or is_admin):
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)


@method_decorator(staff_required, name='dispatch')
class ChangePaymentRequestStatusView(DelegatedViewMixin, PaymentRequestAccessMixin, UpdateView):
    form_class = ChangePaymentRequestStatusForm
    context_name = 'change_payment_status'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.pop('user')
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)

        messenger(
            MESSAGES.UPDATE_PAYMENT_REQUEST_STATUS,
            request=self.request,
            user=self.request.user,
            source=self.object.project,
            related=self.object,
        )

        return response


class DeletePaymentRequestView(DeleteView):
    model = PaymentRequest

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.can_user_delete(request.user):
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)

    @transaction.atomic()
    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)

        messenger(
            MESSAGES.DELETE_PAYMENT_REQUEST,
            request=self.request,
            user=self.request.user,
            source=self.project,
            related=self.object,
        )

        return response

    def get_success_url(self):
        return self.project.get_absolute_url()


class PaymentRequestAdminView(PaymentRequestAccessMixin, DelegateableView, DetailView):
    form_views = [
        ChangePaymentRequestStatusView
    ]
    template_name_suffix = '_admin_detail'


class PaymentRequestApplicantView(PaymentRequestAccessMixin, DelegateableView, DetailView):
    form_views = []


class PaymentRequestView(ViewDispatcher):
    admin_view = PaymentRequestAdminView
    applicant_view = PaymentRequestApplicantView


class CreatePaymentRequestView(CreateView):
    model = PaymentRequest
    form_class = CreatePaymentRequestForm

    def dispatch(self, request, *args, **kwargs):
        self.project = Project.objects.get(pk=kwargs['pk'])
        if not request.user.is_apply_staff and not self.project.user == request.user:
            return redirect(self.project)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        return super().get_context_data(project=self.project, **kwargs)

    def form_valid(self, form):
        form.instance.project = self.project
        form.instance.by = self.request.user

        response = super().form_valid(form)

        messenger(
            MESSAGES.REQUEST_PAYMENT,
            request=self.request,
            user=self.request.user,
            source=self.project,
            related=self.object,
        )

        return response


class EditPaymentRequestView(PaymentRequestAccessMixin, UpdateView):
    form_class = EditPaymentRequestForm

    def dispatch(self, request, *args, **kwargs):
        payment_request = self.get_object()
        if not payment_request.can_user_edit(request.user):
            return redirect(payment_request)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)

        messenger(
            MESSAGES.UPDATE_PAYMENT_REQUEST,
            request=self.request,
            user=self.request.user,
            source=self.object.project,
            related=self.object,
        )

        return response


@method_decorator(login_required, name='dispatch')
class PaymentRequestPrivateMedia(UserPassesTestMixin, PrivateMediaView):
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


@method_decorator(staff_required, name='dispatch')
class PaymentRequestListView(SingleTableMixin, FilterView):
    filterset_class = PaymentRequestListFilter
    model = PaymentRequest
    table_class = PaymentRequestsListTable
    template_name = 'application_projects/payment_request_list.html'

    def get_queryset(self):
        return PaymentRequest.objects.order_by('date_to')
