from datetime import timedelta

from django import template

from ..permissions import has_permission
from ..utils import no_pafreviewer_role

register = template.Library()


@register.simple_tag
def has_project_sow_form(project):
    return project.submission.page.specific.sow_forms.exists()


def user_has_approved(project, user):
    """Has the given User already approved the given Project"""
    return project.approvals.filter(by=user).exists()


@register.simple_tag
def user_can_send_for_approval(project, user):
    return (
        user.is_apply_staff
        and project.can_send_for_approval
        and not (no_pafreviewer_role())
    )


@register.simple_tag
def user_can_update_paf_approvers(project, user, request):
    permission, _ = has_permission(
        "paf_approvers_update",
        user,
        object=project,
        raise_exception=False,
        request=request,
    )
    return permission


@register.simple_tag
def user_can_assign_approvers_to_project(project, user, request):
    permission, _ = has_permission(
        "paf_approvers_assign",
        user,
        object=project,
        raise_exception=False,
        request=request,
    )
    return permission


@register.simple_tag
def user_can_update_paf_status(project, user, **kwargs):
    request = kwargs.get("request")
    if request:
        permission, _ = has_permission(
            "paf_status_update",
            user,
            object=project,
            raise_exception=False,
            request=request,
        )
        return permission
    return False


@register.simple_tag
def user_can_edit_project(project, user):
    return project.editable_by(user)


@register.simple_tag
def project_rejected_by_user(project, user):
    """Using for paf approvals sidebar section"""
    # todo: need to find a better way to know request change action on PAF.
    from hypha.apply.activity.models import Activity

    if not user:
        return False
    message = "Requested changes for acceptance"  # picked from activity.adapters.activity_feed.ActivityAdapter messages
    return Activity.actions.filter(
        source_content_type__model="project",
        source_object_id=project.id,
        user__id=user.id,
        message__icontains=message,
    ).exists()


@register.simple_tag
def get_comment_for_requested_approval(requested_approval):
    from hypha.apply.activity.models import Activity

    if requested_approval.updated_at:
        comment = Activity.comments.filter(
            user__id=requested_approval.user.id,
            source_content_type__model="project",
            source_object_id=requested_approval.project.id,
            timestamp__range=(
                requested_approval.updated_at - timedelta(minutes=2),
                requested_approval.updated_at + timedelta(minutes=2),
            ),
        ).first()
        return comment if comment else None
    return None
