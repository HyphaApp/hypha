from django import template
from django.core.exceptions import ObjectDoesNotExist

register = template.Library()


@register.filter
def can_add_determination(user, submission):
    try:
        has_determination = submission.determination
    except ObjectDoesNotExist:
        has_determination = False
    return submission.user_lead_or_admin(user) and not has_determination


@register.filter
def has_draft(user, submission):
    try:
        return submission.user_lead_or_admin(user) and submission.determination.is_draft
    except ObjectDoesNotExist:
        return False
