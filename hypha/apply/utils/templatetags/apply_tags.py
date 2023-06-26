import babel.numbers

from django import template
from django.conf import settings

register = template.Library()


# Get the verbose name of a model instance
@register.filter
def model_verbose_name(instance):
    return instance._meta.verbose_name.title()


@register.filter
def format_number_as_currency(amount):
    try:
        float(str(amount).replace(',', ''))
        return babel.numbers.format_currency(str(amount).replace(',', ''), settings.CURRENCY_CODE, locale=settings.CURRENCY_LOCALE)
    except ValueError:
        return babel.numbers.get_currency_symbol(settings.CURRENCY_CODE, locale=settings.CURRENCY_LOCALE)
