from django import template

from ..permissions import has_permission

register = template.Library()


@register.simple_tag
def user_can_approve_contract(user, project):
    can_approve, _ = has_permission('contract_approve', user, object=project, raise_exception=False)
    return can_approve


@register.simple_tag
def user_can_upload_contract(project, user):
    can_upload, _ = has_permission('contract_upload', user, object=project, raise_exception=False)
    return can_upload
