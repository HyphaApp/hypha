from django.db.models import Count, Exists, OuterRef

from hypha.apply.projects.models import PAFApprovals


def get_paf_for_review(user, is_paf_approval_sequential):
    """Return a queryset of paf approvals ready for user's review"""
    user_groups = list(user.groups.all())

    paf_approvals = PAFApprovals.objects.annotate(
        roles_count=Count("paf_reviewer_role__user_roles")
    ).filter(
        roles_count=len(user_groups),
        approved=False,
    )

    for role in user_groups:
        paf_approvals = paf_approvals.filter(paf_reviewer_role__user_roles__id=role.id)

    if is_paf_approval_sequential:
        blocking_step = PAFApprovals.objects.filter(
            project=OuterRef("project"),
            approved=False,
            paf_reviewer_role__sort_order__lt=OuterRef("paf_reviewer_role__sort_order"),
        )
        paf_approvals = paf_approvals.exclude(Exists(blocking_step))

    return paf_approvals
