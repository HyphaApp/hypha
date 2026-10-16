import csv
import io
from datetime import timedelta

from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django_file_form.uploaded_file import PlaceholderUploadedFile

from .constants import (
    INT_DECLINED,
    INT_FINANCE_PENDING,
    INT_ORG_PENDING,
    INT_PAID,
    INT_PAYMENT_FAILED,
    INT_REQUEST_FOR_CHANGE,
    INT_STAFF_PENDING,
    INT_VENDOR_PENDING,
)
from .models import Project
from .models.invoice import (
    APPROVED_BY_FINANCE,
    APPROVED_BY_STAFF,
    CHANGES_REQUESTED_BY_FINANCE,
    CHANGES_REQUESTED_BY_STAFF,
    DECLINED,
    INVOICE_STATUS_CHOICES,
    PAID,
    PAYMENT_FAILED,
    RESUBMITTED,
    SUBMITTED,
)
from .models.project import (
    INTERNAL_APPROVAL,
    PAF_STATUS_CHOICES,
    PROJECT_PUBLIC_STATUSES,
    PROJECT_STATUS_CHOICES,
    PAFReviewersRole,
)

PROJECT_TITLE_TEMPLATE = "{text} <span class='text-fg-muted'>#{application_id}</span>"


def get_project_title(project):
    return format_html(
        PROJECT_TITLE_TEMPLATE,
        text=project.title,
        application_id=project.application_id,
    )


def no_pafreviewer_role():
    """
    Return True if no PAFReviewerRoles exists
    """
    return not (PAFReviewersRole.objects.exists())


def get_project_status_choices():
    """
    Return available Project status choices by removing the disabled ones
    """
    if no_pafreviewer_role():
        return [
            (status, label)
            for status, label in PROJECT_STATUS_CHOICES
            if status != INTERNAL_APPROVAL
        ]
    return PROJECT_STATUS_CHOICES


def save_project_details(project_id, data):
    project = Project.objects.get(id=project_id)
    project.external_project_information = data
    project.save()


def get_paf_status_display(paf_status):
    return dict(PAF_STATUS_CHOICES)[paf_status]


# Invoices public statuses
def get_invoice_public_status(invoice_status):
    if invoice_status in [
        SUBMITTED,
        RESUBMITTED,
        APPROVED_BY_STAFF,
        CHANGES_REQUESTED_BY_FINANCE,
    ]:
        return _("Pending approval")
    if invoice_status == APPROVED_BY_FINANCE:
        return _("Approved")
    if invoice_status == CHANGES_REQUESTED_BY_STAFF:
        return _("Request for change or more information")
    if invoice_status == DECLINED:
        return _("Declined")
    if invoice_status == PAID:
        return _("Paid")
    if invoice_status == PAYMENT_FAILED:
        return _("Payment failed")


def get_project_status_display_value(project_status):
    return dict(PROJECT_STATUS_CHOICES)[project_status]


def get_project_public_status(project_status):
    return dict(PROJECT_PUBLIC_STATUSES)[project_status]


def get_invoice_status_display_value(invoice_status):
    return dict(INVOICE_STATUS_CHOICES)[invoice_status]


def get_invoice_table_status(invoice_status, is_applicant=False):
    if invoice_status in [SUBMITTED, RESUBMITTED]:
        if is_applicant:
            return INT_ORG_PENDING
        return INT_STAFF_PENDING
    if invoice_status == CHANGES_REQUESTED_BY_STAFF:
        if is_applicant:
            return INT_REQUEST_FOR_CHANGE
        return INT_VENDOR_PENDING
    if invoice_status in [APPROVED_BY_STAFF, CHANGES_REQUESTED_BY_FINANCE]:
        if is_applicant:
            return INT_ORG_PENDING
        return INT_FINANCE_PENDING
    if invoice_status == PAID:
        return INT_PAID
    if invoice_status == DECLINED:
        return INT_DECLINED
    if invoice_status == PAYMENT_FAILED:
        return INT_PAYMENT_FAILED


def export_invoices_to_csv(invoices_iter) -> str:
    """Generate a CSV string from an invoice queryset iterator.

    Columns match those shown in the invoice list table. Add more fields here
    as needed.
    """
    output = io.StringIO()
    fieldnames = [
        "Invoice #",
        "Invoice Date",
        "Status",
        "Submitted",
        "Project Title",
        "Project #",
        "Vendor Name",
        "Invoice Amount",
        "Tags",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for invoice in invoices_iter:
        writer.writerow(
            {
                "Invoice #": invoice.invoice_number or "",
                "Invoice Date": invoice.invoice_date.isoformat()
                if invoice.invoice_date
                else "",
                "Status": invoice.get_status_display(),
                "Submitted": invoice.requested_at.strftime("%Y-%m-%d %H:%M")
                if invoice.requested_at
                else "",
                "Project Title": invoice.project.title,
                "Project #": invoice.project.application_id,
                "Vendor Name": str(invoice.project.user),
                "Invoice Amount": str(invoice.invoice_amount)
                if invoice.invoice_amount is not None
                else "",
                "Tags": ", ".join(tag.name for tag in invoice.tags.all()),
            }
        )

    return output.getvalue()


def get_placeholder_file(initial_file):
    if not isinstance(initial_file, list):
        return PlaceholderUploadedFile(
            initial_file.filename, size=initial_file.size, file_id=initial_file.name
        )
    return [
        PlaceholderUploadedFile(f.filename, size=f.size, file_id=f.name)
        for f in initial_file
    ]


def export_projects_to_csv(projects_list, csv_stream):
    header_row = [
        "Submission #",
        "Title",
        "Organization",
        "Status",
        "Lead",
        "Fund",
        "Round",
        "Reporting",
        "Last payment request",
        "End Date",
    ]
    data_list = []

    for project in projects_list:
        reporting_status = ""
        if hasattr(project, "report_config"):
            if project.report_config.is_up_to_date():
                reporting_status = "Up to date"
            else:
                reporting_status = (
                    f"{project.report_config.outstanding_reports()} outstanding"
                )

        values = {
            header_row[0]: project.submission.id,
            header_row[1]: project.title,
            header_row[2]: project.submission.form_data.get("organization_name", ""),
            header_row[3]: project.get_status_display(),
            header_row[4]: project.lead,
            header_row[5]: project.submission.page,
            header_row[6]: project.submission.round,
            header_row[7]: reporting_status,
            header_row[8]: project.last_payment_request,
            header_row[9]: project.end_date,
        }
        data_list.append(values)
    # Columns will be in header_row order with values matched by key in data_list (order within each notwithstanding).
    writer = csv.DictWriter(csv_stream, fieldnames=header_row, restval="")
    writer.writeheader()
    for data in data_list:
        writer.writerow(data)


def format_trimmed_amount(value):
    """Trimmed decimal string for table/CSV amounts; em dash when absent.

    Mirrors the amount input so ledger values never gain or lose precision.

    """
    if value is None:
        return "—"
    # Lazy import: forms.project depends on modules that import this file.
    from .forms.project import TrimmedDecimalInput

    return TrimmedDecimalInput().format_value(value)


def format_local_minute(value):
    """Compact table display for entry datetimes: the active timezone (the
    user's zone when a deployment activates one, else the server's), rounded
    to the nearest minute, space separator, no zone suffix.

    The CSV export keeps strict RFC 3339 (T separator, full precision).

    """
    if timezone.is_aware(value):
        rounded = timezone.localtime(value).replace(tzinfo=None)
    else:
        rounded = value.replace(tzinfo=None)
    if rounded.second >= 30:
        rounded += timedelta(minutes=1)
    return rounded.replace(second=0, microsecond=0).strftime("%Y-%m-%d %H:%M")


def export_disbursements_to_csv(disbursements, csv_stream):
    """Export disbursements (typically the filtered ledger queryset) to CSV.

    One row per disbursement; the contract's requested/approved amounts
    repeat on each of its rows, mirroring the table. The row leads with
    submission # and project. Amounts are bare and trimmed with the currency
    in its own column; dates are strict RFC 3339 (T separator, full
    precision), including the full updated_at; absent contract amounts
    export as empty strings.

    """
    header_row = [
        "Submission #",
        "Project",
        "Disbursement date",
        "Date recorded",
        "Updated at",
        "Contract",
        "Contract requested",
        "Contract approved",
        "Currency",
        "Amount disbursed",
        "Notes",
    ]
    data_list = []

    for disbursement in disbursements:
        contract = disbursement.contract
        project = contract.project
        values = {
            header_row[0]: project.submission_id,
            header_row[1]: project.title,
            header_row[2]: disbursement.date.isoformat(),
            header_row[3]: disbursement.created_at.isoformat(),
            header_row[4]: disbursement.updated_at.isoformat(),
            header_row[5]: f"#{contract.pk}",
            header_row[6]: (
                format_trimmed_amount(contract.amount_requested)
                if contract.amount_requested is not None
                else ""
            ),
            header_row[7]: (
                format_trimmed_amount(contract.amount_approved)
                if contract.amount_approved is not None
                else ""
            ),
            header_row[8]: contract.currency or "",
            header_row[9]: format_trimmed_amount(disbursement.amount),
            header_row[10]: disbursement.notes,
        }
        data_list.append(values)
    # Columns will be in header_row order with values matched by key in data_list (order within each notwithstanding).
    writer = csv.DictWriter(csv_stream, fieldnames=header_row, restval="")
    writer.writeheader()
    for data in data_list:
        writer.writerow(data)
