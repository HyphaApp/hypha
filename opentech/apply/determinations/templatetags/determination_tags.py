from django import template
from django.core.exceptions import ObjectDoesNotExist

from opentech.apply.determinations.models import NEEDS_MORE_INFO
from opentech.apply.funds.workflow import DETERMINATION_PHASES

register = template.Library()


@register.filter
def is_lead_or_admin(user, submission):
    return submission.user_lead_or_admin(user)


@register.filter
def can_add_determination(user, submission):
    """
    A determination can be added when
    - the user is admin or the submission lead
    - the submission is in a discussion phase
    - there was not determination response (i.e. accepted / rejected)
    """
    try:
        has_determination_response = submission.determination.submitted
    except ObjectDoesNotExist:
        has_determination_response = False

    return submission.user_lead_or_admin(user) \
        and submission.status in DETERMINATION_PHASES \
        and not has_determination_response


@register.filter
def has_determination_draft(user, submission):
    try:
        return submission.user_lead_or_admin(user) and submission.determination.is_draft
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
