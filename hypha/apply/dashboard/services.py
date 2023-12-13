from django.db.models import Count

from hypha.apply.projects.models import PAFApprovals


def get_paf_for_review(user, is_paf_approval_sequential):
    """Return a list of paf approvals ready for user's review"""

    paf_approvals = PAFApprovals.objects.annotate(
        roles_count=Count("paf_reviewer_role__user_roles")
    ).filter(
        roles_count=len(list(user.groups.all())),
        approved=False,
    )

    for role in user.groups.all():
        paf_approvals = paf_approvals.filter(paf_reviewer_role__user_roles__id=role.id)

    if is_paf_approval_sequential:
        all_matched_paf_approvals = list(paf_approvals)
        for matched_paf_approval in all_matched_paf_approvals:
            if matched_paf_approval.project.paf_approvals.filter(
                paf_reviewer_role__sort_order__lt=matched_paf_approval.paf_reviewer_role.sort_order,
                approved=False,
            ).exists():
                paf_approvals = paf_approvals.exclude(id=matched_paf_approval.id)

    return paf_approvals
