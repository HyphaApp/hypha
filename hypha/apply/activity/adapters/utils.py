from collections import defaultdict

from django.db.models import Count
from django.utils.translation import gettext as _

from hypha.apply.activity.options import MESSAGES
from hypha.apply.projects.models import ProjectSettings
from hypha.apply.projects.models.payment import (
    APPROVED_BY_FINANCE,
    CHANGES_REQUESTED_BY_STAFF,
    DECLINED,
    PAID,
    PAYMENT_FAILED,
    RESUBMITTED,
    SUBMITTED,
)
from hypha.apply.users.models import User
from hypha.apply.users.roles import (
    CONTRACTING_GROUP_NAME,
    FINANCE_GROUP_NAME,
    STAFF_GROUP_NAME,
)


def link_to(target, request):
    if target and hasattr(target, "get_absolute_url"):
        return request.scheme + "://" + request.get_host() + target.get_absolute_url()


def group_reviewers(reviewers):
    groups = defaultdict(list)
    for reviewer in reviewers:
        groups[reviewer.role].append(reviewer.reviewer)
    return groups


def reviewers_message(reviewers):
    messages = []
    for role, reviewers_ in group_reviewers(reviewers).items():
        message = ", ".join(str(reviewer) for reviewer in reviewers_)
        if role:
            message += _(" as {role}").format(role=str(role))
        message += "."
        messages.append(message)
    return messages


def is_transition(message_type):
    return message_type in [MESSAGES.TRANSITION, MESSAGES.BATCH_TRANSITION]


def is_ready_for_review(message_type):
    return message_type in [MESSAGES.READY_FOR_REVIEW, MESSAGES.BATCH_READY_FOR_REVIEW]


def is_invoice_public_transition(invoice):
    if invoice.status in [
        SUBMITTED,
        RESUBMITTED,
        CHANGES_REQUESTED_BY_STAFF,
        DECLINED,
        PAID,
        PAYMENT_FAILED,
    ]:
        return True
    if invoice.status == APPROVED_BY_FINANCE:
        return True
    return False


def is_reviewer_update(message_type):
    return message_type in [
        MESSAGES.REVIEWERS_UPDATED,
        MESSAGES.BATCH_REVIEWERS_UPDATED,
    ]


def get_compliance_email(target_user_gps=None):
    project_settings = ProjectSettings.objects.first()

    if project_settings is None:
        # TODO: what to do when this isn't configured??
        return []
    target_user_emails = []
    if not target_user_gps or not isinstance(target_user_gps, list):
        return [project_settings.staff_gp_email]
    if CONTRACTING_GROUP_NAME in target_user_gps:
        if project_settings.contracting_gp_email:
            target_user_emails.extend([project_settings.contracting_gp_email])
        else:
            contracting_users_email = []
            for user in User.objects.contracting():
                contracting_users_email.append(user.email)
            target_user_emails.extend(contracting_users_email)
    if FINANCE_GROUP_NAME in target_user_gps:
        if project_settings.finance_gp_email:
            target_user_emails.extend([project_settings.finance_gp_email])
        else:
            finance_users_email = []
            for user in User.objects.finances():
                finance_users_email.append(user.email)
            target_user_emails.extend(finance_users_email)
    if STAFF_GROUP_NAME in target_user_gps:
        if project_settings.staff_gp_email:
            target_user_emails.extend([project_settings.staff_gp_email])
        else:
            staff_users_email = []
            for user in User.objects.staff():
                staff_users_email.append(user.email)
            target_user_emails.extend(staff_users_email)
    return target_user_emails


def get_users_for_groups(groups, user_queryset=None, exact_match=False):
    """
    It will return the user queryset with the mentioned groups,

    **NOTE: exact_match and user_queryset are not working together(for now). Set either one of them.
    """
    if groups:
        if not user_queryset:
            if exact_match:
                user_queryset = (
                    User.objects.active()
                    .annotate(group_count=Count("groups"))
                    .filter(group_count=len(groups), groups__name=groups.pop().name)
                )
            else:
                user_queryset = User.objects.active().filter(
                    groups__name=groups.pop().name
                )
        else:
            user_queryset = user_queryset.filter(groups__name=groups.pop().name)
        return get_users_for_groups(groups, user_queryset=user_queryset)
    else:
        return user_queryset if user_queryset is not None else set()
