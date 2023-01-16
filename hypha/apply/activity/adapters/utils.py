from collections import defaultdict

from django.utils.translation import gettext as _

from hypha.apply.activity.options import MESSAGES

from hypha.apply.projects.models import ProjectSettings


def link_to(target, request):
    if target and hasattr(target, 'get_absolute_url'):
        return request.scheme + '://' + request.get_host() + target.get_absolute_url()


def group_reviewers(reviewers):
    groups = defaultdict(list)
    for reviewer in reviewers:
        groups[reviewer.role].append(reviewer.reviewer)
    return groups


def reviewers_message(reviewers):
    messages = []
    for role, reviewers_ in group_reviewers(reviewers).items():
        message = ', '.join(str(reviewer) for reviewer in reviewers_)
        if role:
            message += _(' as {role}').format(role=str(role))
        message += '.'
        messages.append(message)
    return messages


def is_transition(message_type):
    return message_type in [MESSAGES.TRANSITION, MESSAGES.BATCH_TRANSITION]


def is_ready_for_review(message_type):
    return message_type in [MESSAGES.READY_FOR_REVIEW, MESSAGES.BATCH_READY_FOR_REVIEW]


def is_reviewer_update(message_type):
    return message_type in [MESSAGES.REVIEWERS_UPDATED, MESSAGES.BATCH_REVIEWERS_UPDATED]


def get_compliance_email():
    project_settings = ProjectSettings.objects.first()

    if project_settings is None:
        # TODO: what to do when this isn't configured??
        return []

    return [project_settings.compliance_email]
