import decimal
from datetime import timedelta

from django import template
from django.utils.translation import gettext_lazy as _

from hypha.apply.activity.models import Activity
from hypha.apply.activity.templatetags.activity_tags import display_for
from hypha.apply.projects.constants import (
    INVOICE_STATUS_CLASSNAME_MAP,
)
from hypha.apply.projects.models.payment import PAID
from hypha.apply.projects.models.project import (
    CLOSING,
    COMPLETE,
    INVOICING_AND_REPORTING,
)
from hypha.apply.projects.utils import (
    get_invoice_public_status,
    get_invoice_table_status,
)

register = template.Library()


@register.simple_tag
def can_change_status(invoice, user):
    return invoice.can_user_change_status(user)


@register.simple_tag
def can_show_paid_date(invoice):
    if invoice.status == PAID and invoice.paid_date:
        return True
    return False


@register.simple_tag
def can_delete(invoice, user):
    return invoice.can_user_delete(user)


@register.simple_tag
def can_edit(invoice, user):
    return invoice.can_user_edit(user)


@register.simple_tag
def percentage(value, total):
    if not total:
        return decimal.Decimal(0)

    unrounded_total = (value / total) * 100

    # round using Decimal since we're dealing with currency
    rounded_total = unrounded_total.quantize(
        decimal.Decimal("0.0"),
        rounding=decimal.ROUND_DOWN,
    )

    return rounded_total


@register.simple_tag
def project_can_have_invoices(project):
    if project.status in [INVOICING_AND_REPORTING, CLOSING, COMPLETE]:
        return True
    return False


@register.simple_tag
def get_invoice_form(invoice, user):
    from hypha.apply.projects.views.payment import ChangeInvoiceStatusForm

    form = ChangeInvoiceStatusForm(instance=invoice, user=user)
    if form:
        form.name = "change_invoice_status"
        return form
    return None


@register.simple_tag
def get_invoice_form_id(form, invoice):
    return f"{form.name}-{invoice.id}"


@register.simple_tag
def extract_status(activity, user):
    if activity and user:
        invoice_activity_message = display_for(activity, user)
        invoice_status = invoice_activity_message.replace(
            "Updated Invoice status to: ", ""
        ).replace(".", "")
        if " by " not in str(invoice_status) and not user.is_applicant:
            if activity.user.is_apply_staff:
                user_role = "staff"
            elif activity.user.is_finance:
                user_role = "finance"
            else:
                user_role = "vendor"
            return _("{status} by {user_role}").format(
                status=invoice_status, user_role=user_role
            )
        return invoice_status
    return ""


@register.simple_tag
def display_invoice_status_for_user(user, invoice):
    if user.is_apply_staff or user.is_contracting or user.is_finance:
        return invoice.status_display
    return get_invoice_public_status(invoice_status=invoice.status)


@register.simple_tag
def get_comment_for_invoice_action(invoice, action):
    if action and invoice:
        return Activity.comments.filter(
            timestamp__range=(
                action.timestamp - timedelta(minutes=1),
                action.timestamp + timedelta(minutes=1),
            ),
            related_content_type__model="invoice",
            related_object_id=invoice.id,
        ).first()


@register.filter
def invoice_status_to_classname(invoice_status):
    return INVOICE_STATUS_CLASSNAME_MAP.get(invoice_status, "badge")


@register.simple_tag
def display_invoice_table_status_for_user(status, user):
    return get_invoice_table_status(status, is_applicant=user.is_applicant)
