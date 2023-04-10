import decimal

from django import template

from hypha.apply.projects.models.project import CLOSING, COMPLETE, IN_PROGRESS, ProjectSettings

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
        decimal.Decimal('0.0'),
        rounding=decimal.ROUND_DOWN,
    )

    return rounded_total


@register.simple_tag
def can_edit_deliverables(invoice, user):
    return invoice.can_user_edit_deliverables(user)


@register.simple_tag
def user_can_view_invoices(project, user):
    if project.status in [IN_PROGRESS, CLOSING, COMPLETE]:
        return True
    return False


@register.simple_tag
def user_can_add_invoices(project, user):
    if project.status == IN_PROGRESS and (user.is_apply_staff or user == project.user):
        return True
    return False


@register.simple_tag
def is_vendor_setup(request):
    project_settings = ProjectSettings.for_request(request)
    return project_settings.vendor_setup_required
