from django.conf import settings
from django.utils.translation import gettext_lazy as _

from .models.payment import (
    APPROVED_BY_FINANCE,
    APPROVED_BY_STAFF,
    CHANGES_REQUESTED_BY_FINANCE,
    CHANGES_REQUESTED_BY_STAFF,
    DECLINED,
    PAID,
    PAYMENT_FAILED,
    RESUBMITTED,
    SUBMITTED,
)

# INT refers Invoice table
INT_STAFF_PENDING = _("Staff pending")
INT_FINANCE_PENDING = _("Finance pending")
INT_VENDOR_PENDING = _("Vendor pending")

# duplicate statuses
INT_DECLINED = _("Declined")
INT_PAID = _("Paid")
INT_PAYMENT_FAILED = _("Payment failed")

# INVOICE_TABLE_STATUSES = [INT_STAFF_PENDING, INT_FINANCE_PENDING, INT_VENDOR_PENDING, INT_DECLINED,
#                           INT_PAID, INT_PAYMENT_FAILED]

INT_ORG_PENDING = _("{} pending").format(settings.ORG_SHORT_NAME)
INT_REQUEST_FOR_CHANGE = _("Request for change")

# INVOICE_TABLE_PUBLIC_STATUSES = [INT_ORG_PENDING, INT_REQUEST_FOR_CHANGE,
#                                  INT_DECLINED, INT_PAID, INT_PAYMENT_FAILED]

INVOICE_STATUS_CLASSNAME_MAP = {
    INT_ORG_PENDING: "badge badge-warning",
    INT_PAID: "badge badge-success",
    INT_REQUEST_FOR_CHANGE: "badge badge-info",
    INT_PAYMENT_FAILED: "badge badge-error",
    INT_DECLINED: "badge badge-error",
}

statuses_and_table_statuses_mapping = {
    INT_FINANCE_PENDING: [APPROVED_BY_STAFF, APPROVED_BY_FINANCE],
    INT_STAFF_PENDING: [SUBMITTED, RESUBMITTED, CHANGES_REQUESTED_BY_FINANCE],
    INT_VENDOR_PENDING: [CHANGES_REQUESTED_BY_STAFF],
    INT_PAID: [PAID],
    INT_DECLINED: [DECLINED],
    INT_PAYMENT_FAILED: [PAYMENT_FAILED],
}
