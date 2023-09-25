import decimal

from django import template

from hypha.apply.activity.templatetags.activity_tags import display_for
from hypha.apply.projects.models.payment import INVOICE_STATUS_BG_COLORS
from hypha.apply.projects.models.project import (
    CLOSING,
    COMPLETE,
    INVOICING_AND_REPORTING,
    ProjectSettings,
)
from hypha.apply.projects.utils import get_invoice_public_status

register = template.Library()


@register.simple_tag
def can_change_status(invoice, user):
    return invoice.can_user_change_status(user)


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
def can_edit_deliverables(invoice, user):
    return invoice.can_user_edit_deliverables(user)


@register.simple_tag
def user_can_view_invoices(project, user):
    if project.status in [INVOICING_AND_REPORTING, CLOSING, COMPLETE]:
        return True
    return False


@register.simple_tag
def user_can_add_invoices(project, user):
    if project.status == INVOICING_AND_REPORTING and (
        user.is_apply_staff or user == project.user
    ):
        return True
    return False


@register.simple_tag
def is_vendor_setup(request):
    project_settings = ProjectSettings.for_request(request)
    return project_settings.vendor_setup_required


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
        return invoice_activity_message.replace(
            "Updated Invoice status to: ", ""
        ).replace(".", "")
    return ""


@register.simple_tag
def display_invoice_status_for_user(user, invoice):
    if user.is_apply_staff or user.is_contracting or user.is_finance:
        return invoice.status_display
    return get_invoice_public_status(invoice_status=invoice.status)


@register.filter
def invoice_status_colour(invoice_status):
    return INVOICE_STATUS_BG_COLORS.get(invoice_status, "gray")
