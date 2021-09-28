from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin

from hypha.apply.activity.messaging import MESSAGES, messenger
from hypha.apply.users.decorators import staff_or_finance_required
from hypha.apply.utils.storage import PrivateMediaView
from hypha.apply.utils.views import DelegateableView, DelegatedViewMixin, ViewDispatcher

from ..filters import InvoiceListFilter, PaymentRequestListFilter
from ..forms import (
    ChangeInvoiceStatusForm,
    ChangePaymentRequestStatusForm,
    CreateInvoiceForm,
    CreatePaymentRequestForm,
    EditInvoiceForm,
    EditPaymentRequestForm,
)
from ..models.payment import Invoice, PaymentRequest
from ..models.project import Project
from ..tables import InvoiceListTable, PaymentRequestsListTable


@method_decorator(login_required, name='dispatch')
class PaymentRequestAccessMixin(UserPassesTestMixin):
    model = PaymentRequest

    def test_func(self):
        if self.request.user.is_apply_staff:
            return True

        if self.request.user.is_finance:
            return True

        if self.request.user == self.get_object().project.user:
            return True

        return False


@method_decorator(login_required, name='dispatch')
class InvoiceAccessMixin(UserPassesTestMixin):
    model = Invoice

    def get_object(self):
        project = get_object_or_404(Project, pk=self.kwargs['pk'])
        return get_object_or_404(project.invoices.all(), pk=self.kwargs['invoice_pk'])

    def test_func(self):
        if self.request.user.is_apply_staff:
            return True

        if self.request.user.is_finance:
            return True

        if self.request.user == self.get_object().project.user:
            return True

        return False


@method_decorator(staff_or_finance_required, name='dispatch')
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


@method_decorator(staff_or_finance_required, name='dispatch')
class ChangeInvoiceStatusView(DelegatedViewMixin, InvoiceAccessMixin, UpdateView):
    form_class = ChangeInvoiceStatusForm
    context_name = 'change_invoice_status'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.pop('user')
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)

        messenger(
            MESSAGES.UPDATE_INVOICE_STATUS,
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


class DeleteInvoiceView(DeleteView):
    model = Invoice

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.can_user_delete(request.user):
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)

    @transaction.atomic()
    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)

        messenger(
            MESSAGES.DELETE_INVOICE,
            request=self.request,
            user=self.request.user,
            source=self.object.project,
            related=self.object.project,
        )

        return response

    def get_success_url(self):
        return self.object.project.get_absolute_url()


class PaymentRequestAdminView(PaymentRequestAccessMixin, DelegateableView, DetailView):
    form_views = [
        ChangePaymentRequestStatusView
    ]
    template_name_suffix = '_admin_detail'


class PaymentRequestApplicantView(PaymentRequestAccessMixin, DelegateableView, DetailView):
    form_views = []


class PaymentRequestView(ViewDispatcher):
    admin_view = PaymentRequestAdminView
    finance_view = PaymentRequestAdminView
    applicant_view = PaymentRequestApplicantView


class InvoiceAdminView(InvoiceAccessMixin, DelegateableView, DetailView):
    form_views = [
        ChangeInvoiceStatusView
    ]
    template_name_suffix = '_admin_detail'

    def get_context_data(self, **kwargs):
        object = self.get_object()
        deliverables = object.project.deliverables.all()
        return super().get_context_data(
            **kwargs,
            deliverables=deliverables
        )


class InvoiceApplicantView(InvoiceAccessMixin, DelegateableView, DetailView):
    form_views = []


class InvoiceView(ViewDispatcher):
    admin_view = InvoiceAdminView
    finance_view = InvoiceAdminView
    applicant_view = InvoiceApplicantView


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

        # Required for django-file-form: delete temporary files for the new files
        # that are uploaded.
        form.delete_temporary_files()
        return response


class CreateInvoiceView(CreateView):
    model = Invoice
    form_class = CreateInvoiceForm

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
            MESSAGES.CREATE_INVOICE,
            request=self.request,
            user=self.request.user,
            source=self.project,
            related=self.object,
        )

        # Required for django-file-form: delete temporary files for the new files
        # that are uploaded.
        form.delete_temporary_files()
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

        # Required for django-file-form: delete temporary files for the new files
        # that are uploaded.
        form.delete_temporary_files()
        return response


class EditInvoiceView(InvoiceAccessMixin, UpdateView):
    form_class = EditInvoiceForm

    def dispatch(self, request, *args, **kwargs):
        invoice = self.get_object()
        if not invoice.can_user_edit(request.user):
            return redirect(invoice)
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()

        initial["supporting_documents"] = [
            document.document for document in self.object.supporting_documents.all()
        ]
        return initial

    def form_valid(self, form):
        response = super().form_valid(form)

        messenger(
            MESSAGES.UPDATE_INVOICE,
            request=self.request,
            user=self.request.user,
            source=self.object.project,
            related=self.object,
        )

        # Required for django-file-form: delete temporary files for the new files
        # that are uploaded.
        form.delete_temporary_files()
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

        if self.request.user.is_finance:
            return True

        if self.request.user == self.payment_request.project.user:
            return True

        return False


@method_decorator(login_required, name='dispatch')
class InvoicePrivateMedia(UserPassesTestMixin, PrivateMediaView):
    raise_exception = True

    def dispatch(self, *args, **kwargs):
        invoice_pk = self.kwargs['invoice_pk']
        project_pk = self.kwargs['pk']
        self.project = get_object_or_404(Project, pk=project_pk)
        self.invoice = get_object_or_404(self.project.invoices.all(), pk=invoice_pk)

        return super().dispatch(*args, **kwargs)

    def get_media(self, *args, **kwargs):
        file_pk = kwargs.get('file_pk')
        if not file_pk:
            return self.invoice.document

        document = get_object_or_404(self.invoice.supporting_documents, pk=file_pk)
        return document.document

    def test_func(self):
        if self.request.user.is_apply_staff:
            return True

        if self.request.user.is_finance:
            return True

        if self.request.user == self.invoice.project.user:
            return True

        return False


@method_decorator(staff_or_finance_required, name='dispatch')
class PaymentRequestListView(SingleTableMixin, FilterView):
    filterset_class = PaymentRequestListFilter
    model = PaymentRequest
    table_class = PaymentRequestsListTable
    template_name = 'application_projects/payment_request_list.html'

    def get_queryset(self):
        return PaymentRequest.objects.order_by('date_to')


@method_decorator(staff_or_finance_required, name='dispatch')
class InvoiceListView(SingleTableMixin, FilterView):
    filterset_class = InvoiceListFilter
    model = Invoice
    table_class = InvoiceListTable
    template_name = 'application_projects/invoice_list.html'

    def get_queryset(self):
        return Invoice.objects.order_by('date_to')
