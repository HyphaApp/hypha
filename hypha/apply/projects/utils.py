from django.conf import settings
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
from .models import Deliverable, Project
from .models.payment import (
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


def fetch_and_save_deliverables(project_id):
    """
    Fetch deliverables from the enabled payment service and save it in Hypha.
    """
    if settings.INTACCT_ENABLED:
        from hypha.apply.projects.services.sageintacct.utils import fetch_deliverables

        project = Project.objects.get(id=project_id)
        program_project_id = project.program_project_id
        deliverables = fetch_deliverables(program_project_id)
        save_deliverables(project_id, deliverables)


def save_deliverables(project_id, deliverables=None):
    """
    TODO: List of deliverables coming from IntAcct is
    not verified yet from the team. This method may need
    revision when that is done.
    """
    if deliverables is None:
        deliverables = []
    if deliverables:
        remove_deliverables_from_project(project_id)
    project = Project.objects.get(id=project_id)
    new_deliverable_list = []
    for deliverable in deliverables:
        item_id = deliverable["ITEMID"]
        item_name = deliverable["ITEMNAME"]
        qty_remaining = int(float(deliverable["QTY_REMAINING"]))
        price = deliverable["PRICE"]
        extra_information = {
            "UNIT": deliverable["UNIT"],
            "DEPARTMENTID": deliverable["DEPARTMENTID"],
            "PROJECTID": deliverable["PROJECTID"],
            "LOCATIONID": deliverable["LOCATIONID"],
            "CLASSID": deliverable["CLASSID"],
            "BILLABLE": deliverable["BILLABLE"],
            "CUSTOMERID": deliverable["CUSTOMERID"],
        }
        new_deliverable_list.append(
            Deliverable(
                external_id=item_id,
                name=item_name,
                available_to_invoice=qty_remaining,
                unit_price=price,
                extra_information=extra_information,
                project=project,
            )
        )
    Deliverable.objects.bulk_create(new_deliverable_list)


def remove_deliverables_from_project(project_id):
    project = Project.objects.get(id=project_id)
    deliverables = project.deliverables.all()
    for deliverable in deliverables:
        deliverable.project = None
        deliverable.save()


def fetch_and_save_project_details(project_id, external_projectid):
    """
    Fetch and save project contract information from enabled payment service.
    """
    if settings.INTACCT_ENABLED:
        from hypha.apply.projects.services.sageintacct.utils import (
            fetch_project_details,
        )

        data = fetch_project_details(external_projectid)
        save_project_details(project_id, data)


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


def create_invoice(invoice):
    """
    Creates invoice at enabled payment service.
    """
    if settings.INTACCT_ENABLED:
        from hypha.apply.projects.services.sageintacct.utils import (
            create_intacct_invoice,
        )

        create_intacct_invoice(invoice)


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
