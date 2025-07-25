from typing import Optional

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpRequest
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from hypha.apply.activity.models import Activity

from ..models.payment import Invoice
from ..models.project import ContractDocumentCategory, DocumentCategory, Project


@login_required
def partial_project_lead(request, pk):
    project = get_object_or_404(Project, submission__pk=pk)
    return render(
        request, "application_projects/partials/project_lead.html", {"object": project}
    )


@login_required
def partial_project_title(request, pk):
    project = get_object_or_404(Project, submission__pk=pk)
    return render(
        request, "application_projects/partials/project_title.html", {"object": project}
    )


@login_required
def partial_project_information(request, pk):
    project = get_object_or_404(Project, submission__pk=pk)
    return render(
        request,
        "application_projects/partials/project_information.html",
        {"object": project},
    )


@login_required
@require_GET
def partial_supporting_documents(request, pk):
    project = get_object_or_404(Project, submission__pk=pk)
    ctx = {"object": project}
    ctx["all_document_categories"] = DocumentCategory.objects.all()
    ctx["remaining_document_categories"] = DocumentCategory.objects.filter(
        ~Q(packet_files__project=project)
    )
    return render(
        request, "application_projects/partials/supporting_documents.html", ctx
    )


@login_required
@require_GET
def partial_contracting_documents(request, pk):
    project = get_object_or_404(Project, submission__pk=pk)
    ctx = {"object": project}
    ctx["all_contract_document_categories"] = ContractDocumentCategory.objects.all()
    ctx["remaining_contract_document_categories"] = (
        ContractDocumentCategory.objects.filter(
            ~Q(contract_packet_files__project=project)
        )
    )
    # contracts
    contracts = project.contracts.select_related(
        "approver",
    ).order_by("-created_at")

    latest_contract = contracts.first()
    ctx["contract"] = latest_contract
    return render(
        request,
        "application_projects/partials/contracting_category_documents.html",
        ctx,
    )


@login_required
def partial_get_invoice_status_table(
    request: HttpRequest, pk: int, rejected: Optional[bool] = False
):
    """
    Partial to get the invoice status table

    Args:
        request: request used to retrieve partial
        pk: PK of the project to retrieve invoices for
        rejected: retrieve rejected invoices, by default only retrieves not rejected invoices

    Returns:
        HttpResponse containing the table of requested invoices
    """
    invoices = get_object_or_404(Project, pk=pk).invoices

    return render(
        request,
        "application_projects/partials/invoice_status_table.html",
        context={
            "invoices": invoices.rejected if rejected else invoices.not_rejected,
            "user": request.user,
            "rejected": rejected,
        },
    )


@login_required
def partial_get_invoice_status(request: HttpRequest, pk: int, invoice_pk: int):
    """
    Partial to get the invoice status for invoice detail view

    Args:
        request: request used to retrieve partial
        pk: ID of the associated project
        invoice_pk: ID of the invoice to retrieve the status of

    Returns:
        HttpResponse containing the status line of requested invoice
    """
    invoice = get_object_or_404(Invoice, pk=invoice_pk)
    user = request.user
    invoice_activities = Activity.actions.filter(
        related_content_type__model="invoice", related_object_id=invoice.id
    ).visible_to(user)

    return render(
        request,
        "application_projects/partials/invoice_status.html",
        context={
            "object": invoice,
            "latest_activity": invoice_activities.first(),
            "activities": invoice_activities[1:],
            "user": user,
        },
    )


@login_required
def partial_get_invoice_detail_actions(request: HttpRequest, pk: int, invoice_pk: int):
    """
    Partial to get the actions for the invoice detail view

    Args:
        request: request used to retrieve partial
        pk: ID of the associated project
        invoice_pk: ID of the invoice to retrieve the status of

    Returns:
        HttpResponse containing the status line of requested invoice
    """
    invoice = get_object_or_404(Invoice, pk=invoice_pk)
    user = request.user

    return render(
        request,
        "application_projects/partials/invoice_detail_actions.html",
        context={"object": invoice, "user": user},
    )
