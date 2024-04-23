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
def format_number_as_currency(amount):
    try:
        float(str(amount).replace(",", ""))
        return babel.numbers.format_currency(
            str(amount).replace(",", ""),
            settings.CURRENCY_CODE,
            locale=settings.CURRENCY_LOCALE,
        )
    except ValueError:
        return babel.numbers.get_currency_symbol(
            settings.CURRENCY_CODE, locale=settings.CURRENCY_LOCALE
        )


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
