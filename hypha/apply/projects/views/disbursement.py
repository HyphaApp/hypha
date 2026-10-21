"""Create, update, and delete views for Disbursement (staff/finance only).

Disbursements are entered in a modal on the project page; on save the user is
returned to the project page (see ``get_success_url``). An activity/messenger
notice is emitted for each create/update/delete; the amount is included in the
notice, the note is not.

"""

from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.generic import CreateView, DeleteView, UpdateView

from hypha.apply.activity.messaging import MESSAGES, messenger
from hypha.apply.users.decorators import staff_or_finance_required

from ..forms import DisbursementForm
from ..models import Disbursement, Project


@method_decorator(staff_or_finance_required, name="dispatch")
class CreateDisbursementView(SuccessMessageMixin, CreateView):
    model = Disbursement
    form_class = DisbursementForm
    template_name = "application_projects/modals/disbursement_form.html"
    success_message = _("Disbursement added")

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, submission__pk=kwargs["pk"])
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
        return reverse("funds:submissions:project", kwargs={"pk": self.kwargs["pk"]})


@method_decorator(staff_or_finance_required, name="dispatch")
class EditDisbursementView(SuccessMessageMixin, UpdateView):
    model = Disbursement
    form_class = DisbursementForm
    template_name = "application_projects/modals/disbursement_form.html"
    success_message = _("Disbursement updated")

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, submission__pk=kwargs["pk"])
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
        return reverse("funds:submissions:project", kwargs={"pk": self.kwargs["pk"]})


@method_decorator(staff_or_finance_required, name="dispatch")
class DeleteDisbursementView(DeleteView):
    model = Disbursement
    template_name = "application_projects/modals/disbursement_confirm_delete.html"

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, submission__pk=kwargs["pk"])
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
        return reverse("funds:submissions:project", kwargs={"pk": self.kwargs["pk"]})
