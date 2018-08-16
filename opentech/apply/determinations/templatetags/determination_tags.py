from django import template
from django.core.exceptions import ObjectDoesNotExist

from ..views import can_create_determination

register = template.Library()


@register.filter
def can_add_determination(user, submission):
    return can_create_determination(user, submission)
