from django import template

from hypha.apply.funds.permissions import has_permission

register = template.Library()


@register.simple_tag
def can_invite_coapplicant(user, submission):
    permission, _ = has_permission(
        "co_applicant_invite",
        user,
        object=submission,
        raise_exception=False,
    )
    return permission


@register.simple_tag
def can_update_coapplicant(user, invite):
    permission, _ = has_permission(
        "co_applicants_update",
        user,
        object=invite,
        raise_exception=False,
    )
    return permission
