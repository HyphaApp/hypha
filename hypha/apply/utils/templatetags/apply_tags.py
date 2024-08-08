import decimal

import babel.numbers
from django import template
from django.conf import settings
from django.template.defaultfilters import stringfilter

from hypha.core.navigation import get_primary_navigation_items

register = template.Library()


# Get the verbose name of a model instance
@register.filter
def model_verbose_name(instance):
    return instance._meta.verbose_name.title()


@register.filter
def format_number_as_currency(amount: float | decimal.Decimal | str | None):
    """Formats a number as currency"""
    if amount is None:
        amount = 0

    return babel.numbers.format_currency(
        amount,
        settings.CURRENCY_CODE,
        locale=settings.CURRENCY_LOCALE,
    )


@register.simple_tag
def get_currency_symbol():
    """Gets the currency symbol based on system settings"""
    return babel.numbers.get_currency_symbol(
        settings.CURRENCY_CODE, locale=settings.CURRENCY_LOCALE
    )


@register.filter
def subtract(total_submissions: int, req_amt_submissions: int) -> int:
    """Subtracts two numbers

    Primarily used in calculating the the number of submissions to be excluded in the results view

    Args:
        total_submissions: number to be subtracted from
        req_amt_submissions: number to subtract

    Returns:
        int: the difference between the given values
    """
    return total_submissions - req_amt_submissions


@register.filter(is_safe=True)
@stringfilter
def truncatechars_middle(value, arg):
    try:
        ln = int(arg)
    except ValueError:
        return value
    if len(value) <= ln:
        return value
    else:
        return "{}...{}".format(value[: ln // 2], value[-((ln + 1) // 2) :])


@register.simple_tag
def primary_navigation_items(user):
    return get_primary_navigation_items(user)
