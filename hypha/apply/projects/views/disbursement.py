"""Create, update, and delete views for Disbursement (staff/finance only).

Disbursements are entered in a modal on the project page; on save the user is
returned to the project page (see ``get_success_url``). An activity/messenger
notice is emitted for each create/update/delete; the amount is included in the
notice, the note is not.

"""

from django.conf import settings
from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction
from django.db.models import F, Sum
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.generic import CreateView, DeleteView, UpdateView
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin

from hypha.apply.activity.messaging import MESSAGES, messenger
from hypha.apply.users.decorators import (
    staff_admin_required,
    staff_or_finance_required,
)

from ..filters import DisbursementListFilter
from ..forms import DisbursementForm
from ..models import Disbursement, Project
from ..payments import PaymentsFlow
from ..tables import AdminDisbursementListTable
from ..utils import export_disbursements_to_csv, format_trimmed_amount


@method_decorator(staff_or_finance_required, name="dispatch")
class CreateDisbursementView(SuccessMessageMixin, CreateView):
    model = Disbursement
    form_class = DisbursementForm
    template_name = "application_projects/modals/disbursement_form.html"
    success_message = _("Disbursement added")

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, pk=kwargs["pk"])
        self.contract = get_object_or_404(
            self.project.contracts.all(), pk=kwargs["contract_pk"]
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            contract=self.contract,
            project=self.project,
            value=_("Save"),
            **kwargs,
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["contract"] = self.contract
        return kwargs

    def form_valid(self, form):
        form.instance.contract = self.contract
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        messenger(
            MESSAGES.CREATE_DISBURSEMENT,
            request=self.request,
            user=self.request.user,
            source=self.project,
            related=self.object,
        )
        return response

    def get_success_url(self):
        return self.project.get_absolute_url()


@method_decorator(staff_or_finance_required, name="dispatch")
class EditDisbursementView(SuccessMessageMixin, UpdateView):
    model = Disbursement
    form_class = DisbursementForm
    template_name = "application_projects/modals/disbursement_form.html"
    success_message = _("Disbursement updated")

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, pk=kwargs["pk"])
        self.contract = get_object_or_404(
            self.project.contracts.all(), pk=kwargs["contract_pk"]
        )
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        return get_object_or_404(
            self.contract.disbursements.all(), pk=self.kwargs["disbursement_pk"]
        )

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            contract=self.contract,
            project=self.project,
            value=_("Update"),
            **kwargs,
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["contract"] = self.contract
        return kwargs

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        messenger(
            MESSAGES.UPDATE_DISBURSEMENT,
            request=self.request,
            user=self.request.user,
            source=self.project,
            related=self.object,
        )
        return response

    def get_success_url(self):
        return self.project.get_absolute_url()


@method_decorator(staff_or_finance_required, name="dispatch")
class DeleteDisbursementView(DeleteView):
    model = Disbursement
    template_name = "application_projects/modals/disbursement_confirm_delete.html"

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, pk=kwargs["pk"])
        self.contract = get_object_or_404(
            self.project.contracts.all(), pk=kwargs["contract_pk"]
        )
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        return get_object_or_404(
            self.contract.disbursements.all(), pk=self.kwargs["disbursement_pk"]
        )

    @transaction.atomic
    def form_valid(self, form):
        # Capture before super().form_valid() deletes the instance; the
        # activity notice includes the amount, which is still on the object.
        disbursement = self.object
        response = super().form_valid(form)
        messenger(
            MESSAGES.DELETE_DISBURSEMENT,
            request=self.request,
            user=self.request.user,
            source=self.project,
            related=disbursement,
        )
        return response

    def get_success_url(self):
        return self.project.get_absolute_url()


@method_decorator(staff_admin_required, name="dispatch")
class DisbursementListView(SingleTableMixin, FilterView):
    """The admin ledger: every disbursement across every project.

    Admin-only (Staff Admin group or superuser) because it exposes every
    project's money movement in one place. Gated on the DISBURSEMENTS
    payments flow, like the per-project disbursements section. The table
    filters on the disbursement's own date, not the date it was entered, so
    financial reports can be generated for particular periods; ``?format=csv``
    exports the filtered rows.

    """

    filterset_class = DisbursementListFilter
    queryset = Disbursement.objects.select_related("contract__project__submission")
    table_class = AdminDisbursementListTable
    template_name = "application_projects/disbursement_list.html"

    def dispatch(self, request, *args, **kwargs):
        if settings.PROJECTS_PAYMENTS_FLOW != PaymentsFlow.DISBURSEMENTS:
            raise Http404("Disbursements are not the active payments flow")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # The CSV response discards page context, so skip the totals query.
        if self.request.GET.get("format") != "csv":
            context["disbursements_total"] = self.get_total_display()
        return context

    def get_total_display(self):
        """Amount/currency pairs summed over the filtered rows, one pair per
        currency (uncoded rows form their own pair without a code), e.g.
        "499.03 USD, 809.03 MXN". Value only: the template renders it as
        "Total disbursed (N records matching this filter)" between the
        filters and the table. Table rows and per-project displays keep a
        single numeric value ("Multiple currencies" when needed); only this
        page summary elaborates every pair.

        """
        currency_groups = (
            self.object_list.order_by()
            .values("contract__currency")
            .annotate(total=Sum("amount"))
            .order_by(F("contract__currency").asc(nulls_last=True))
        )
        pairs = []
        for group in currency_groups:
            amount = format_trimmed_amount(group["total"])
            currency = group["contract__currency"]
            pairs.append(f"{amount} {currency}" if currency else amount)
        return ", ".join(pairs)

    def render_to_response(self, context, **response_kwargs):
        if self.request.GET.get("format") == "csv":
            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = 'attachment; filename="disbursements.csv"'
            # table.data.data carries the table's applied ordering (e.g.
            # ?sort=), so the export matches what the user sees.
            export_disbursements_to_csv(context["table"].data.data, response)
            return response
        return super().render_to_response(context, **response_kwargs)
