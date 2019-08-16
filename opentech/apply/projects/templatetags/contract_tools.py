from django import template

from ..models import COMMITTED

register = template.Library()


@register.simple_tag
def user_can_upload_contract(project, user):
    if user.is_apply_staff:
        return project.status != COMMITTED

    # Does the Project have any unapproved contracts?
    contracts = project.contracts.order_by('-created_at')
    latest_approved = contracts.filter(approver__isnull=False).first()
    if latest_approved is None:
        return True

    latest_unapproved = contracts.filter(approver__isnull=True).first()
    if latest_unapproved and latest_unapproved.created_at > latest_approved:
        return True

    return False
