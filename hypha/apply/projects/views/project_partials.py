from typing import Optional

from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.db.models import Model, Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET
from rolepermissions.checkers import has_object_permission

from hypha.apply.activity.models import Activity

from ..models.payment import Invoice
from ..models.project import (
    ContractDocumentCategory,
    DocumentCategory,
    Project,
    ProjectFormPointer,
    ProjectSOW,
)
from ..permissions import has_permission


def get_accessible_project(request: HttpRequest, pk: int) -> Project:
    """Retrieve a project, raising if the requesting user has no access to it"""
    project = get_object_or_404(Project, pk=pk)
    has_permission("project_access", request.user, object=project, raise_exception=True)
    return project


def get_accessible_invoice(request: HttpRequest, pk: int, invoice_pk: int) -> Invoice:
    """Retrieve an invoice scoped to its project, raising if the user can't see it"""
    project = get_object_or_404(Project, pk=pk)
    invoice = get_object_or_404(project.invoices, pk=invoice_pk)
    has_permission("invoice_access", request.user, object=invoice, raise_exception=True)
    return invoice


def get_object_activity(request: HttpRequest, obj: Model) -> HttpResponse:
    """A generic view function to be leveraged by more specific object views

    The caller is responsible for resolving `obj` and for checking that the
    requesting user is allowed to see it.

    Args:
        request: request used to retrieve partial
        obj: the object to get activity for

    Returns:
        A rendered object_status.html template containing all status/activity relating to the specific object
    """
    user = request.user

    related_type_pk = ContentType.objects.get_for_model(obj).pk

    activities = (
        Activity.objects.filter(
            related_content_type=related_type_pk, related_object_id=obj.pk
        )
        .exclude(current=False)
        .visible_to(user)
    )

    preview_activity = (
        Activity.actions.filter(
            related_content_type=related_type_pk, related_object_id=obj.pk
        )
        .visible_to(user)
        .first()
    )

    return render(
        request,
        "application_projects/partials/object_status.html",
        context={
            "object": obj,
            "preview_activity": preview_activity,
            "activities": activities,
            "user": user,
            # Determine if the collapsible be open by default
            "open": True if request.GET.get("open") == "true" else False,
        },
    )


@login_required
@require_GET
def partial_project_lead(request, pk):
    project = get_accessible_project(request, pk)
    return render(
        request, "application_projects/partials/project_lead.html", {"object": project}
    )


@login_required
@require_GET
def partial_project_title(request, pk):
    project = get_accessible_project(request, pk)
    return render(
        request, "application_projects/partials/project_title.html", {"object": project}
    )


@login_required
@require_GET
def partial_project_information(request, pk):
    project = get_accessible_project(request, pk)
    return render(
        request,
        "application_projects/partials/project_information.html",
        {"object": project},
    )


@login_required
@require_GET
def partial_supporting_documents(request, pk):
    project = get_accessible_project(request, pk)
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
    project = get_accessible_project(request, pk)
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
@require_GET
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
    invoices = get_accessible_project(request, pk).invoices

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
@require_GET
def partial_get_invoice_status(request: HttpRequest, pk: int, invoice_pk: int):
    """
    Partial to get the invoice status for invoice detail view

    Args:
        request: request used to retrieve partial
        pk: PK of the project the invoice belongs to
        invoice_pk: ID of the invoice to retrieve the status of

    Returns:
        HttpResponse containing the activity of requested invoice
    """
    invoice = get_accessible_invoice(request, pk, invoice_pk)
    return get_object_activity(request, invoice)


@login_required
@require_GET
def partial_get_report_status(request: HttpRequest, pk: int, report_pk: int):
    """
    Partial to get the report status for the report detail view

    Args:
        request: request used to retrieve partial
        pk: PK of the project the report belongs to
        report_pk: ID of the report to retrieve the status of

    Returns:
        HttpResponse containing the activity of requested report
    """
    project = get_accessible_project(request, pk)
    report = get_object_or_404(project.reports, pk=report_pk)
    # `project_access` alone would expose future/skipped reports, mirror the
    # check made by `ReportDetailView.dispatch`.
    if not has_object_permission("view_report", request.user, report):
        raise PermissionDenied
    return get_object_activity(request, report)


@login_required
@require_GET
def partial_get_sow_status(request: HttpRequest, pk: int, sow_pk: int):
    """
    Partial to get the SOW status for SOW detail view

    Args:
        request: request used to retrieve partial
        pk: PK of the project the SOW belongs to
        sow_pk: ID of the SOW to retrieve the status of

    Returns:
        HttpResponse containing activity
    """
    project = get_accessible_project(request, pk)
    sow = get_object_or_404(ProjectSOW, pk=sow_pk, project=project)
    return get_object_activity(request, sow)


@login_required
@require_GET
def partial_get_pf_status(request: HttpRequest, pk: int, pfp_pk: int):
    """
    Partial to get the project form status for approval detail view

    Args:
        request: request used to retrieve partial
        pk: PK of the project the project form belongs to
        pfp_pk: ID of the ProjectFormPointer to retrieve status of the project form for

    Returns:
        HttpResponse containing the activity of the requested project form
    """
    project = get_accessible_project(request, pk)
    pfp = get_object_or_404(ProjectFormPointer, pk=pfp_pk, project=project)
    return get_object_activity(request, pfp)


@login_required
@require_GET
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
    invoice = get_accessible_invoice(request, pk, invoice_pk)
    user = request.user

    return render(
        request,
        "application_projects/partials/invoice_detail_actions.html",
        context={"object": invoice, "user": user},
    )


@login_required
@require_GET
def partial_get_invoice_tags(request: HttpRequest, pk: int, invoice_pk: int):
    invoice = get_accessible_invoice(request, pk, invoice_pk)
    return render(
        request,
        "application_projects/partials/invoice_tags.html",
        context={"object": invoice},
    )
