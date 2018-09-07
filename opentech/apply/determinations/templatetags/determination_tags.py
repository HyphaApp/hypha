from django import template
from django.db.models import ObjectDoesNotExist

from ..views import can_create_determination, can_edit_determination

register = template.Library()


@register.filter
def show_determination_button(user, submission):
    try:
        return can_edit_determination(user, submission.determinations.active(), submission)
    except ObjectDoesNotExist:
        return can_create_determination(user, submission)
