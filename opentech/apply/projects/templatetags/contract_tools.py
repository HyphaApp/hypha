from django import template

from ..models import COMMITTED

register = template.Library()


@register.simple_tag
def user_can_upload_contract(project, user):
    if user.is_apply_staff:
        return project.status != COMMITTED

    # Does the Project have any unapproved contracts?
    latest_contract = project.contracts.order_by('-created_at').first()

    # No contract ever uploaded - nothing to do
    if not latest_contract:
        return False

    # Latest contract approved - nothing to do
    if latest_contract.approver:
        return False

    # Contract is either:
    #  - Unsigned: Applicant needs to sign it.
    #  - Signed: Applicant is waiting on approval and may need to upload a new
    #    version because my scanning was bad.
    return True
