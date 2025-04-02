from django import template

from hypha.apply.projects.models.projects import (
    PROJECT_PUBLIC_STATUSES,
    PROJECT_STATUS_CHOICES,
)

register = template.Library()


@register.inclusion_tag("dashboard/includes/project_status_bar.html")
def project_status_bar(current_status, user, author=False, css_class=""):
    is_applicant = user == author if author else user.is_applicant

    statuses = PROJECT_STATUS_CHOICES

    if is_applicant:
        statuses = PROJECT_PUBLIC_STATUSES

    # Get the display name for the current status
    current_status_name = dict(PROJECT_STATUS_CHOICES).get(
        current_status, current_status
    )

    return {
        "statuses": statuses,
        "current_status_index": [status for status, _ in PROJECT_STATUS_CHOICES].index(
            current_status
        ),
        "current_status": current_status,
        "current_status_name": current_status_name,
        "class": css_class,
    }
