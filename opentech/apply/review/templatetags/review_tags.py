from django import template
from django.utils.safestring import mark_safe

from ..models import MAYBE, NO, YES

register = template.Library()


TRAFFIC_LIGHT_COLORS = {
    YES: {
        'color': 'green',
        'value': 'Y',
    },
    MAYBE: {
        'color': 'amber',
        'value': 'M',
    },
    NO: {
        'color': 'red',
        'value': 'N'
    }
}

TRAFFIC_LIGHT_TEMPLATE = '<span class="traffic-light traffic-light--{color}">{value}</span>'


@register.filter()
def traffic_light(value):
    try:
        return mark_safe(TRAFFIC_LIGHT_TEMPLATE.format(**TRAFFIC_LIGHT_COLORS[value]))
    except KeyError:
        return '-'
