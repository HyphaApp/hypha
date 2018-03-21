from django import template
from django.utils.safestring import mark_safe

from ..models import MAYBE, NO, YES, Review

register = template.Library()


TRAFFIC_LIGHT_COLORS = {
    YES: 'green',
    MAYBE: 'amber',
    NO: 'red',
}

TRAFFIC_LIGHT_TEMPLATE = '<span class="traffic-light traffic-light__{color}"></span>'


@register.filter()
def traffic_light(value):
    try:
        return mark_safe(TRAFFIC_LIGHT_TEMPLATE.format(color=TRAFFIC_LIGHT_COLORS[value]))
    except KeyError:
        return '-'


@register.filter
def can_review(user, submission):
    return submission.can_review(user)
