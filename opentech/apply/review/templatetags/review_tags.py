from django import template
from django.urls import reverse
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


@register.filter
def can_review(user, submission):
    return submission.can_review(user)

@register.filter
def has_draft(user, submission):
    return submission.can_review(user) and submission.reviews.filter(author=user, is_draft=True).exists()

@register.filter
def draft_url(user, submission):
    return reverse('apply:reviews:draft', args=(submission.id, submission.reviews.get(author=user, is_draft=True).id))
