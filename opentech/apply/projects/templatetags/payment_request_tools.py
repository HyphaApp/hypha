from django import template

from ..models import CHANGES_REQUESTED, DECLINED, PAID, SUBMITTED

register = template.Library()


@register.simple_tag
def can_change_status(payment_request, user):
    if not user.is_apply_staff:
        return False  # Users can't change status

    if payment_request.status in (PAID, DECLINED):
        return False

    return True


@register.simple_tag
def can_delete(payment_request, user):
    return payment_request.user_can_delete(user)


@register.simple_tag
def user_can_edit(payment_request, user):
    # staff or applicant can edit when in SUBMITTED
    if payment_request.status == SUBMITTED:
        return True

    # applicant can edit when in CHANGES_REQUESTED
    if payment_request.status == CHANGES_REQUESTED and user.is_applicant:
        return True

    return False
