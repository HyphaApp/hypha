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
from .models.payments import (
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
from .models.projects import (
    INTERNAL_APPROVAL,
    PAF_STATUS_CHOICES,
    PROJECT_PUBLIC_STATUSES,
    PROJECT_STATUS_CHOICES,
    PAFReviewersRole,
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


def get_placeholder_file(initial_file):
    if not isinstance(initial_file, list):
        return PlaceholderUploadedFile(
            initial_file.filename, size=initial_file.size, file_id=initial_file.name
        )
    return [
        PlaceholderUploadedFile(f.filename, size=f.size, file_id=f.name)
        for f in initial_file
    ]
