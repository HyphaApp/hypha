from django import template

from ..models.project import WAITING_FOR_APPROVAL, ProjectSettings
from ..permissions import has_permission

register = template.Library()


@register.simple_tag
def has_project_sow_form(project):
    return project.submission.page.specific.sow_forms.exists()


def user_has_approved(project, user):
    """Has the given User already approved the given Project"""
    return project.approvals.filter(by=user).exists()


@register.simple_tag
def user_can_send_for_approval(project, user):
    return user.is_apply_staff and project.can_send_for_approval


@register.simple_tag
def user_can_update_paf_approvers(project, user, request):
    from hypha.apply.activity.adapters.utils import get_users_for_groups
    if project.status != WAITING_FOR_APPROVAL:
        return False
    if user == project.lead:
        return True
    if not project.paf_approvals.exists():
        return False

    project_settings = ProjectSettings.for_request(request)
    if project_settings.paf_approval_sequential:
        next_paf_approval = project.paf_approvals.filter(approved=False).first()
        if next_paf_approval:
            if next_paf_approval.user and user in get_users_for_groups(list(next_paf_approval.paf_reviewer_role.user_roles.all()), exact_match=True):
                return True
        return False
    else:
        approvers_ids = []
        for approval in project.paf_approvals.filter(approved=False, user__isnull=False):
            approvers_ids.extend(assigner.id for assigner in
                                 get_users_for_groups(list(approval.paf_reviewer_role.user_roles.all()),
                                                      exact_match=True))
        if user.id in approvers_ids:
            return True
    return False


@register.simple_tag
def user_can_assign_approvers_to_project(project, user, request):
    from hypha.apply.activity.adapters.utils import get_users_for_groups
    if project.status != WAITING_FOR_APPROVAL:
        return False
    if not project.paf_approvals.exists():
        return False
    project_settings = ProjectSettings.for_request(request)
    if project_settings.paf_approval_sequential:
        next_paf_approval = project.paf_approvals.filter(approved=False).first()
        if next_paf_approval:
            if next_paf_approval.user:
                return False
            else:
                if user in get_users_for_groups(list(next_paf_approval.paf_reviewer_role.user_roles.all()), exact_match=True):
                    return True
            return False
        return False
    else:
        assigners_ids = []
        for approval in project.paf_approvals.filter(approved=False, user__isnull=True):
            assigners_ids.extend(assigner.id for assigner in get_users_for_groups(list(approval.paf_reviewer_role.user_roles.all()), exact_match=True))

        if user.id in assigners_ids:
            return True
    return False


@register.simple_tag
def user_can_update_paf_status(project, user, **kwargs):
    request = kwargs.get('request')
    if request:
        permission, _ = has_permission('paf_status_update', user, object=project, raise_exception=False, request=request)
        return permission
    return False


@register.simple_tag
def user_can_edit_project(project, user):
    return project.editable_by(user)
