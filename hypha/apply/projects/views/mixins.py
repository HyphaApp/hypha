from django.shortcuts import get_object_or_404

from ..models.project import (
    Project,
)


class ProjectByIdMixin:
    def get_object(self):
        pk = self.kwargs.get("project_pk", self.kwargs["pk"])
        return get_object_or_404(Project, pk=pk)


class ContractsMixin(ProjectByIdMixin):
    def get_context_data(self, **kwargs):
        project = self.get_object()
        contracts = project.contracts.select_related(
            "approver",
        ).order_by("-created_at")

        latest_contract = contracts.first()
        contract_to_approve = None
        contract_to_sign = None
        if latest_contract:
            if not latest_contract.signed_by_applicant:
                contract_to_sign = latest_contract
            elif not latest_contract.approver:
                contract_to_approve = latest_contract

        context = super().get_context_data(**kwargs)
        context["contract_to_approve"] = contract_to_approve
        context["contract_to_sign"] = contract_to_sign
        context["contracts"] = contracts.approved()
        context["contract"] = latest_contract
        return context
