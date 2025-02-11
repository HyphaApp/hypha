from typing import List, Tuple

from django.conf import settings

from hypha.apply.projects.models.project import (
    COMPLETE,
    INTERNAL_APPROVAL,
    PROJECT_STATUS_CHOICES,
)


def get_project_status_options() -> List[Tuple[str, str]]:
    """Gets settable project status options

    Filters out complete & internal approval statuses as there isn't value in
    being able to set these
    """
    return filter(
        lambda x: x[0] not in [COMPLETE, INTERNAL_APPROVAL], PROJECT_STATUS_CHOICES
    )


def get_project_default_status() -> Tuple[str, str]:
    """Gets the default project status based off the settings

    If the `PROJECTS_DEFAULT_STATUS` setting is invalid, status will fall back
    to draft
    """
    return next(
        (x for x in PROJECT_STATUS_CHOICES if x[0] == settings.PROJECTS_DEFAULT_STATUS),
        PROJECT_STATUS_CHOICES[0],
    )
