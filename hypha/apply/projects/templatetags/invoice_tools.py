import decimal

from django import template

register = template.Library()


@register.simple_tag
def can_change_status(invoice, user):
    return invoice.can_user_change_status(user)


@register.simple_tag
def can_complete_required_checks(invoice, user):
    return invoice.can_user_complete_required_checks(user)


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
