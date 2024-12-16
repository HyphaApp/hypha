import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    FormView,
    UpdateView,
    View,
)
from django_filters.views import FilterView
from django_htmx.http import (
    HttpResponseClientRefresh,
)
from django_tables2 import SingleTableMixin

from hypha.apply.activity.messaging import MESSAGES, messenger
from hypha.apply.activity.models import APPLICANT, COMMENT, Activity
from hypha.apply.projects.templatetags.invoice_tools import (
    display_invoice_status_for_user,
)
from hypha.apply.todo.options import (
    INVOICE_REQUIRED_CHANGES,
    INVOICE_WAITING_APPROVAL,
    PROJECT_WAITING_INVOICE,
)
from hypha.apply.todo.views import (
    add_task_to_user,
    remove_tasks_for_user,
    remove_tasks_of_related_obj,
)
from hypha.apply.users.decorators import staff_or_finance_required
from hypha.apply.utils.pdfs import html_to_pdf, merge_pdf
from hypha.apply.utils.storage import PrivateMediaView
from hypha.apply.utils.views import (
    DelegateableListView,
    DelegateableView,
    DelegatedViewMixin,
    ViewDispatcher,
)

from ..filters import InvoiceListFilter
from ..forms import (
    BatchUpdateInvoiceStatusForm,
    ChangeInvoiceStatusForm,
    CreateInvoiceForm,
    EditInvoiceForm,
)
from ..models.payment import (
    APPROVED_BY_STAFF,
    CHANGES_REQUESTED_BY_FINANCE,
    CHANGES_REQUESTED_BY_STAFF,
    DECLINED,
    INVOICE_TRANISTION_TO_RESUBMITTED,
    Invoice,
)
from ..models.project import PROJECT_ACTION_MESSAGE_TAG, Project
from ..service_utils import batch_update_invoices_status, handle_tasks_on_invoice_update
from ..tables import AdminInvoiceListTable, FinanceInvoiceTable


@method_decorator(login_required, name="dispatch")
class InvoiceAccessMixin(UserPassesTestMixin):
    model = Invoice

    def get_object(self):
        project = get_object_or_404(Project, pk=self.kwargs["pk"])
        return get_object_or_404(project.invoices.all(), pk=self.kwargs["invoice_pk"])

    def test_func(self):
        if self.request.user.is_apply_staff:
            return True

        if self.request.user.is_finance:
            return True

        if self.request.user == self.get_object().project.user:
            return True

        return False


@method_decorator(staff_or_finance_required, name="dispatch")
class ChangeInvoiceStatusView(InvoiceAccessMixin, View):
    form_class = ChangeInvoiceStatusForm
    context_name = "change_invoice_status"
    model = Invoice
    template = "application_projects/modals/invoice_status_update.html"

    def dispatch(self, request, *args, **kwargs):
        self.object: Invoice = get_object_or_404(Invoice, id=kwargs.get("invoice_pk"))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        if not (form := kwargs.get("form")):
            form = self.form_class(instance=self.object, user=self.request.user)

        form.name = self.context_name

        extras = {
            "form": form,
            "form_id": f"{form.name}-{self.object.id}",
            "invoice_status": display_invoice_status_for_user(
                self.request.user, self.object
            ),
            "value": _("Update status"),
            "object": self.object,
        }

        return {**kwargs, **extras}

    def get(self, *args, **kwargs):
        form_instance = self.form_class(instance=self.object, user=self.request.user)
        form_instance.name = self.context_name

        return render(self.request, self.template, self.get_context_data())

    def post(self, *args, **kwargs):
        # Don't process the post request if the user can't change the status
        old_status = self.object.status
        if not self.object.can_user_change_status(self.request.user):
            return render(
                self.request, self.template, self.get_context_data(), status=403
            )

        form = self.form_class(
            self.request.POST, instance=self.object, user=self.request.user
        )
        if form.is_valid():
            form.save()
            if form.cleaned_data["comment"]:
                invoice_status_change = _(
                    "<p>Invoice status updated to: {status}.</p>"
                ).format(status=self.object.get_status_display())
                comment = f"<p>{self.object.comment}</p>"

                message = invoice_status_change + comment

                Activity.objects.create(
                    user=self.request.user,
                    type=COMMENT,
                    source=self.object.project,
                    timestamp=timezone.now(),
                    message=message,
                    visibility=APPLICANT,
                    related_object=self.object,
                )

            if (
                self.request.user.is_apply_staff
                and self.object.status == APPROVED_BY_STAFF
            ):
                self.object.save()
                messenger(
                    MESSAGES.APPROVE_INVOICE,
                    request=self.request,
                    user=self.request.user,
                    source=self.object.project,
                    related=self.object,
                )

            messenger(
                MESSAGES.UPDATE_INVOICE_STATUS,
                request=self.request,
                user=self.request.user,
                source=self.object.project,
                related=self.object,
            )

            handle_tasks_on_invoice_update(old_status=old_status, invoice=self.object)
            htmx_headers = {"invoicesUpdated": None, "showMessage": "Invoice updated."}
            if self.object.status == DECLINED:
                htmx_headers.update({"rejectedInvoicesUpdated": None})
            return HttpResponse(
                status=204, headers={"HX-Trigger": json.dumps(htmx_headers)}
            )

        return render(
            self.request, self.template, self.get_context_data(form=form), status=400
        )


class DeleteInvoiceView(DeleteView):
    model = Invoice

    def get_object(self):
        project = get_object_or_404(Project, pk=self.kwargs["pk"])
        return get_object_or_404(project.invoices.all(), pk=self.kwargs["invoice_pk"])

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.can_user_delete(request.user):
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)

    @transaction.atomic()
    def form_valid(self, form):
        # remove all tasks related to this invoice irrespective of code and users/user_group
        remove_tasks_of_related_obj(related_obj=self.object)

        response = super().form_valid(form)

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
    form_views = []
    template_name_suffix = "_admin_detail"

    def get_context_data(self, **kwargs):
        invoice = self.get_object()
        project = invoice.project
        deliverables = project.deliverables.all()
        return super().get_context_data(**kwargs, deliverables=deliverables)


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
        self.project = Project.objects.get(pk=kwargs["pk"])
        if not request.user.is_apply_staff and not self.project.user == request.user:
            return redirect(self.project)
        return super().dispatch(request, *args, **kwargs)

    def buttons(self):
        yield ("submit", "primary", _("Save"))

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            project=self.project, buttons=self.buttons(), **kwargs
        )

    def form_valid(self, form):
        form.instance.project = self.project
        form.instance.by = self.request.user

        response = super().form_valid(form)

        if form.cleaned_data["message_for_pm"]:
            invoice_status_change = _("<p>Invoice added.</p>")

            message_for_pm = f'<p>{form.cleaned_data["message_for_pm"]}</p>'

            message = invoice_status_change + message_for_pm

            Activity.objects.create(
                user=self.request.user,
                type=COMMENT,
                source=self.project,
                timestamp=timezone.now(),
                message=message,
                visibility=APPLICANT,
                related_object=self.object,
            )

        messenger(
            MESSAGES.CREATE_INVOICE,
            request=self.request,
            user=self.request.user,
            source=self.project,
            related=self.object,
        )

        if len(self.project.invoices.all()) == 1:
            # remove Project waiting invoices task for applicant on first invoice
            remove_tasks_for_user(
                code=PROJECT_WAITING_INVOICE,
                user=self.project.user,
                related_obj=self.project,
            )

        # add Invoice waiting approval task for Staff group
        add_task_to_user(
            code=INVOICE_WAITING_APPROVAL,
            user=self.object.project.lead,
            related_obj=self.object,
        )

        messages.success(
            self.request, _("Invoice added"), extra_tags=PROJECT_ACTION_MESSAGE_TAG
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

    def buttons(self):
        yield ("submit", "primary", _("Save"))
        if self.object.can_user_delete(self.request.user):
            yield ("delete", "warning", _("Delete"))

    def get_initial(self):
        initial = super().get_initial()
        initial["supporting_documents"] = [
            document.document for document in self.object.supporting_documents.all()
        ]
        return initial

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            project=self.object.project, buttons=self.buttons(), **kwargs
        )

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if "delete" in form.data:
            return redirect(
                "apply:projects:invoice-delete",
                pk=self.object.project.id,
                invoice_pk=self.object.id,
            )
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        old_status = self.object.status
        response = super().form_valid(form)

        if form.cleaned_data:
            if self.object.status in INVOICE_TRANISTION_TO_RESUBMITTED:
                self.object.transition_invoice_to_resubmitted()
                self.object.save()

            if form.cleaned_data["message_for_pm"]:
                invoice_status_change = _(
                    "<p>Invoice status updated to: {status}.</p>"
                ).format(status=self.object.get_status_display())
                message_for_pm = f'<p>{form.cleaned_data["message_for_pm"]}</p>'
                message = invoice_status_change + message_for_pm

                Activity.objects.create(
                    user=self.request.user,
                    type=COMMENT,
                    source=self.object.project,
                    timestamp=timezone.now(),
                    message=message,
                    visibility=APPLICANT,
                    related_object=self.object,
                )

        messenger(
            MESSAGES.UPDATE_INVOICE_STATUS,
            request=self.request,
            user=self.request.user,
            source=self.object.project,
            related=self.object,
        )

        if self.request.user.is_applicant and old_status == CHANGES_REQUESTED_BY_STAFF:
            # remove invoice required changes task for applicant
            remove_tasks_for_user(
                code=INVOICE_REQUIRED_CHANGES,
                user=self.object.project.user,
                related_obj=self.object,
            )

            # add invoice waiting approval task for staff group
            add_task_to_user(
                code=INVOICE_WAITING_APPROVAL,
                user=self.object.project.lead,
                related_obj=self.object,
            )

        if (
            self.request.user.is_apply_staff
            and old_status == CHANGES_REQUESTED_BY_FINANCE
        ):
            # remove invoice required changes task for staff group
            remove_tasks_for_user(
                code=INVOICE_REQUIRED_CHANGES,
                user=self.object.project.lead,
                related_obj=self.object,
            )
            # add invoice waiting approval task for staff group
            add_task_to_user(
                code=INVOICE_WAITING_APPROVAL,
                user=self.object.project.lead,
                related_obj=self.object,
            )

        # Required for django-file-form: delete temporary files for the new files
        # that are uploaded.
        form.delete_temporary_files()
        return response


@method_decorator(login_required, name="dispatch")
class InvoicePrivateMedia(UserPassesTestMixin, PrivateMediaView):
    raise_exception = True

    def dispatch(self, *args, **kwargs):
        invoice_pk = self.kwargs["invoice_pk"]
        project_pk = self.kwargs["pk"]
        self.project = get_object_or_404(Project, pk=project_pk)
        self.invoice = get_object_or_404(self.project.invoices.all(), pk=invoice_pk)

        return super().dispatch(*args, **kwargs)

    def get_media(self, *args, **kwargs):
        # check if the request is for a supporting document
        if file_pk := kwargs.get("file_pk"):
            document = get_object_or_404(self.invoice.supporting_documents, pk=file_pk)
            return document.document

        # if not, then it's for invoice document
        if (
            self.invoice.status == APPROVED_BY_STAFF
            and self.invoice.document.file.name.endswith(".pdf")
        ):
            if activities := Activity.actions.filter(
                related_content_type__model="invoice",
                related_object_id=self.invoice.id,
                message__icontains="Approved by",
            ).visible_to(self.request.user):
                approval_pdf_page = html_to_pdf(
                    render_to_string(
                        "application_projects/pdf_invoice_approved_page.html",
                        context={
                            "invoice": self.invoice,
                            "generated_at": timezone.now(),
                            "activities": activities,
                        },
                        request=self.request,
                    )
                )
                return merge_pdf(self.invoice.document.file, approval_pdf_page)

        return self.invoice.document

    def test_func(self):
        if self.request.user.is_apply_staff:
            return True

        if self.request.user.is_finance:
            return True

        if self.request.user == self.invoice.project.user:
            return True

        return False


@method_decorator(staff_or_finance_required, name="dispatch")
class BatchUpdateInvoiceStatusView(DelegatedViewMixin, FormView):
    form_class = BatchUpdateInvoiceStatusForm
    context_name = "batch_invoice_status_form"
    template_name = "application_projects/modals/batch_invoice_status_update.html"

    def get(self, *args, **kwargs):
        selected_ids = self.request.GET.getlist("selected_ids", "")
        invoices = Invoice.objects.filter(id__in=selected_ids)
        form = self.form_class(user=self.request.user)
        return render(
            self.request,
            self.template_name,
            context={"form": form, "invoices": invoices},
        )

    def post(self, *args, **kwargs):
        form = self.form_class(self.request.POST, user=self.request.user)
        if form.is_valid():
            new_status = form.cleaned_data["invoice_action"]
            invoices = form.cleaned_data["invoices"]
            invoices_old_statuses = {invoice: invoice.status for invoice in invoices}
            batch_update_invoices_status(
                invoices=invoices,
                user=self.request.user,
                status=new_status,
            )

            # add activity feed for batch update invoice status
            projects = Project.objects.filter(
                id__in=[invoice.project.id for invoice in invoices]
            )
            messenger(
                MESSAGES.BATCH_UPDATE_INVOICE_STATUS,
                request=self.request,
                user=self.request.user,
                sources=projects,
                related=invoices,
            )

            # update tasks for selected invoices
            for invoice, old_status in invoices_old_statuses.items():
                handle_tasks_on_invoice_update(old_status, invoice)
            return HttpResponseClientRefresh()
        messages.error(
            self.request,
            mark_safe(_("Sorry something went wrong") + form.errors.as_ul()),
        )
        return HttpResponseClientRefresh()


@method_decorator(staff_or_finance_required, name="dispatch")
class InvoiceListView(SingleTableMixin, FilterView, DelegateableListView):
    form_views = [
        BatchUpdateInvoiceStatusView,
    ]
    filterset_class = InvoiceListFilter
    model = Invoice
    table_class = AdminInvoiceListTable
    template_name = "application_projects/invoice_list.html"

    def get_table_class(self):
        if self.request.user.is_finance:
            return FinanceInvoiceTable
        return super().get_table_class()
