from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin

from hypha.apply.activity.messaging import MESSAGES, messenger
from hypha.apply.activity.models import ALL, COMMENT, Activity
from hypha.apply.users.decorators import staff_or_finance_required
from hypha.apply.utils.storage import PrivateMediaView
from hypha.apply.utils.views import DelegateableView, DelegatedViewMixin, ViewDispatcher

from ..filters import InvoiceListFilter
from ..forms import ChangeInvoiceStatusForm, CreateInvoiceForm, EditInvoiceForm
from ..models.payment import INVOICE_TRANISTION_TO_RESUBMITTED, Invoice
from ..models.project import Project
from ..tables import InvoiceListTable


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
class ChangeInvoiceStatusView(DelegatedViewMixin, InvoiceAccessMixin, UpdateView):
    form_class = ChangeInvoiceStatusForm
    context_name = 'change_invoice_status'

    def form_valid(self, form):
        response = super().form_valid(form)
        if form.cleaned_data['comment']:
            invoice_status_change = _('<p>Invoice status updated to: {status}.</p>').format(status=self.object.status_display)
            comment = f'<p>{self.object.comment}.</p>'

            message = invoice_status_change + comment

            Activity.objects.create(
                user=self.request.user,
                type=COMMENT,
                source=self.object.project,
                timestamp=timezone.now(),
                message=message,
                visibility=ALL,
                related_object=self.object,
            )

        messenger(
            MESSAGES.UPDATE_INVOICE_STATUS,
            request=self.request,
            user=self.request.user,
            source=self.object.project,
            related=self.object,
        )

        return response


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

        if form.cleaned_data['message_for_pm']:
            invoice_status_change = _('<p>Invoice created.</p>')

            message_for_pm = f'<p>{form.cleaned_data["message_for_pm"]}</p>'

            message = invoice_status_change + message_for_pm

            Activity.objects.create(
                user=self.request.user,
                type=COMMENT,
                source=self.project,
                timestamp=timezone.now(),
                message=message,
                visibility=ALL,
                related_object=self.object,
            )

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
        if form.cleaned_data:
            if self.object.status in INVOICE_TRANISTION_TO_RESUBMITTED:
                self.object.transition_invoice_to_resubmitted()
                self.object.save()

            if form.cleaned_data['message_for_pm']:
                invoice_status_change = _('<p>Invoice status updated to: {status}.</p>').format(status=self.object.status_display)
                message_for_pm = f'<p>{form.cleaned_data["message_for_pm"]}</p>'
                message = invoice_status_change + message_for_pm

                Activity.objects.create(
                    user=self.request.user,
                    type=COMMENT,
                    source=self.object.project,
                    timestamp=timezone.now(),
                    message=message,
                    visibility=ALL,
                    related_object=self.object,
                )

        messenger(
            MESSAGES.UPDATE_INVOICE_STATUS,
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
class InvoiceListView(SingleTableMixin, FilterView):
    filterset_class = InvoiceListFilter
    model = Invoice
    table_class = InvoiceListTable
    template_name = 'application_projects/invoice_list.html'

    def get_queryset(self):
        return Invoice.objects.order_by('date_to')
