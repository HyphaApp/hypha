from django.conf import settings

# INT refers Invoice table
INT_STAFF_PENDING = "Staff pending"
INT_FINANCE_PENDING = "Finance pending"
INT_VENDOR_PENDING = "Vendor pending"

# duplicate statuses
INT_DECLINED = "Declined"
INT_PAID = "Paid"
INT_PAYMENT_FAILED = "Payment failed"

# INVOICE_TABLE_STATUSES = [STAFF_PENDING, FINANCE_PENDING, VENDOR_PENDING, DECLINED, PAID, PAYMENT_FAILED]

INT_ORG_PENDING = "{} pending".format(settings.ORG_SHORT_NAME)
INT_REQUEST_FOR_CHANGE = "Request for change"

# INVOICE_TABLE_PUBLIC_STATUSES = [ORG_PENDING, REQUEST_CHANGE, DECLINED, PAID, PAYMENT_FAILED]


INVOICE_STATUS_BG_COLORS = {
    INT_ORG_PENDING: "bg-yellow-100",
    INT_PAID: "bg-green-100",
    INT_REQUEST_FOR_CHANGE: "bg-blue-100",
    INT_PAYMENT_FAILED: "bg-red-100",
    INT_DECLINED: "bg-pink-100",
}

INVOICE_STATUS_FG_COLORS = {
    INT_ORG_PENDING: "text-yellow-700",
    INT_PAID: "text-green-700",
    INT_REQUEST_FOR_CHANGE: "text-blue-700",
    INT_PAYMENT_FAILED: "text-red-700",
    INT_DECLINED: "text-pink-700",
}
