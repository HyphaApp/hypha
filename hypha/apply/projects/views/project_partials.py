from typing import Optional

from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.db.models import Model, Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from hypha.apply.activity.models import Activity
from hypha.apply.projects.reports.models import Report

from ..models.payment import Invoice
from ..models.project import (
    ContractDocumentCategory,
    DocumentCategory,
    Project,
    ProjectFormPointer,
    ProjectSOW,
)
from ..permissions import has_permission


def _get_accessible_project(request: HttpRequest, project_pk: int) -> Project:
    """Get a project, ensuring the current user is allowed to access it.

    Args:
        request: request used to retrieve the partial
        project_pk: the pk of the project to get

    Returns:
        The project

    Raises:
        Http404: if no project with that pk exists
        PermissionDenied: if the user may not access the project
    """
    project = get_object_or_404(Project, pk=project_pk)
    has_permission("project_access", request.user, object=project, raise_exception=True)
    return project


def _get_object_activity(
    request: HttpRequest,
    object_class: type[Model],
    object_pk: int,
    **filters,
) -> HttpResponse:
    """A generic view function to be leveraged by more specific object views

    Args:
        object_class: the model class of the object to get activity for
        object_pk: the pk of the object to get activity for
        filters: additional lookups used to scope the object, e.g. to its project

    Returns:
        A rendered object_status.html template containing all status/activity relating to the specific object
    """
    object = get_object_or_404(object_class, pk=object_pk, **filters)
    user = request.user

    related_type_pk = ContentType.objects.get_for_model(object_class).pk

    activities = (
        Activity.objects.filter(
            related_content_type=related_type_pk, related_object_id=object_pk
        )
        .exclude(current=False)
        .visible_to(user)
    )

    preview_activity = (
        Activity.actions.filter(
            related_content_type=related_type_pk, related_object_id=object_pk
        )
        .visible_to(user)
        .first()
    )

    return render(
        request,
        "application_projects/partials/object_status.html",
        context={
            "object": object,
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
    project = _get_accessible_project(request, pk)
    return render(
        request, "application_projects/partials/project_lead.html", {"object": project}
    )


@login_required
@require_GET
def partial_project_title(request, pk):
    project = _get_accessible_project(request, pk)
    return render(
        request, "application_projects/partials/project_title.html", {"object": project}
    )


@login_required
@require_GET
def partial_project_information(request, pk):
    project = _get_accessible_project(request, pk)
    return render(
        request,
        "application_projects/partials/project_information.html",
        {"object": project},
    )


@login_required
@require_GET
def partial_supporting_documents(request, pk):
    project = _get_accessible_project(request, pk)
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
    project = _get_accessible_project(request, pk)
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
    invoices = _get_accessible_project(request, pk).invoices

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
def partial_get_invoice_status(
    request: HttpRequest, pk: int, invoice_pk: int, *args, **kwargs
):
    """
    Partial to get the invoice status for invoice detail view

    Args:
        request: request used to retrieve partial
        pk: ID of the associated project
        invoice_pk: ID of the invoice to retrieve the status of

    Returns:
        HttpResponse containing the activity of requested invoice
    """
    project = _get_accessible_project(request, pk)
    return _get_object_activity(request, Invoice, invoice_pk, project=project)


@login_required
@require_GET
def partial_get_report_status(
    request: HttpRequest, pk: int, report_pk: int, *args, **kwargs
):
    """
    Partial to get the report status for report detail view

    Args:
        request: request used to retrieve partial
        pk: ID of the associated project
        report_pk: ID of the report to retrieve the status of

    Returns:
        HttpResponse containing the activity of requested report
    """
    project = _get_accessible_project(request, pk)
    return _get_object_activity(request, Report, report_pk, project=project)


@login_required
@require_GET
def partial_get_sow_status(request: HttpRequest, pk: int, sow_pk: int, *args, **kwargs):
    """
    Partial to get the SOW status for SOW detail view

    Args:
        request: request used to retrieve partial
        pk: ID of the associated project
        sow_pk: ID of the SOW to retrieve the status of

    Returns:
        HttpResponse containing activity
    """
    project = _get_accessible_project(request, pk)
    return _get_object_activity(request, ProjectSOW, sow_pk, project=project)


@login_required
@require_GET
def partial_get_pf_status(request: HttpRequest, pk: int, pfp_pk: int, *args, **kwargs):
    """
    Partial to get the project form status for approval detail view

    Args:
        request: request used to retrieve partial
        pk: ID of the associated project
        pfp_pk: ID of the ProjectFormPointer to retrieve status of the project form for

    Returns:
        HttpResponse containing the activity of requested project form
    """
    project = _get_accessible_project(request, pk)
    return _get_object_activity(request, ProjectFormPointer, pfp_pk, project=project)


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
    project = _get_accessible_project(request, pk)
    invoice = get_object_or_404(Invoice, pk=invoice_pk, project=project)
    user = request.user

    return render(
        request,
        "application_projects/partials/invoice_detail_actions.html",
        context={"object": invoice, "user": user},
    )


@login_required
@require_GET
def partial_get_invoice_tags(request: HttpRequest, pk: int, invoice_pk: int):
    project = _get_accessible_project(request, pk)
    invoice = get_object_or_404(Invoice, pk=invoice_pk, project=project)
    return render(
        request,
        "application_projects/partials/invoice_tags.html",
        context={"object": invoice},
    )
