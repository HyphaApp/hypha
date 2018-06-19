from django import template
from django.core.exceptions import ObjectDoesNotExist

from opentech.apply.determinations.models import NEEDS_MORE_INFO
from opentech.apply.funds.workflow import DETERMINATION_PHASES

register = template.Library()


@register.filter
def is_lead_or_admin(user, submission):
    return submission.has_permission_to_add_determination(user)


@register.filter
def can_add_determination(user, submission):
    if submission.status not in DETERMINATION_PHASES:
        return False

    if not submission.has_permission_to_add_determination(user):
        return False

    try:
        return not submission.determination.submitted
    except ObjectDoesNotExist:
        return True


@register.filter
def has_determination_draft(user, submission):
    try:
        return submission.has_permission_to_add_determination(user) and submission.determination.is_draft
    except ObjectDoesNotExist:
        return False


@register.filter
def pending_determination(submission, user):
    """
    The submission doesn't have a determination response (accepted / rejected), does not require more info
    and is not in a determination state.
    """
    if not submission.active or 'more_info' in submission.status:
        return False

    if submission.status in DETERMINATION_PHASES:
        try:
            return not submission.determination \
                   or (submission.determination.is_draft and not user.is_apply_staff) \
                   or submission.determination.outcome == NEEDS_MORE_INFO
        except ObjectDoesNotExist:
            return True

    return True
