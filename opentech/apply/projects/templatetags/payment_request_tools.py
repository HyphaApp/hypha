from django import template

from ..models import DECLINED, PAID

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
