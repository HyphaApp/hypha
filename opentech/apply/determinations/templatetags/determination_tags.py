from django import template
from django.core.exceptions import ObjectDoesNotExist

from opentech.apply.determinations.models import NEEDS_MORE_INFO
from opentech.apply.funds.workflow import DETERMINATION_PHASES

register = template.Library()


@register.filter
def can_add_determination(user, submission):
    if not submission.can_have_determination:
        return False

    if not submission.has_permission_to_add_determination(user):
        return False

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
    Check when to show the determination block.

    The submission doesn't have a determination response (accepted / rejected), does not require more info
    and is not in a determination state.
    """
    if not submission.active or 'more_info' in submission.status:
        return False

    if not submission.in_determination_phase:
        return True

    try:
        # No determination at all -> pending
        if not submission.determination:
            return True

        # When the determination is in draft, only the lead and admins can see that as such
        if submission.has_permission_to_add_determination(user):
            return False

        if submission.determination.is_draft:
            return True

        # There is a determination, that is not draft. Yet we are in a determination phase (i.e. in discussion)
        # If the determination outcome is that it needs
        return submission.determination.outcome == NEEDS_MORE_INFO

    except ObjectDoesNotExist:
        # No determination and we are ina determination phase
        return not submission.has_permission_to_add_determination(user)
