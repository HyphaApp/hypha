"""
Workflow System Documentation

This package implements a flexible workflow system for managing application states
and transitions. The system is built on the following key concepts:

- Workflow: Overall process definition containing stages and phases
- Stage: Major sections of the workflow (e.g. Request, Proposal)
- Phase: Individual states within a stage
- Transition: Allowed movements between phases

Key Components:
- models/: Core workflow model classes
- definitions/: Workflow configuration definitions
- registry.py: Central workflow registration and lookup
- permissions.py: Permission checking system
"""

from .constants import (
    DETERMINATION_OUTCOMES,
    DRAFT_STATE,
    INITIAL_STATE,
    STAGE_CHANGE_ACTIONS,
    UserPermissions,
)
from .models.stage import Stage
from .registry import (
    PHASES,
    STATUSES,
    WORKFLOWS,
    accepted_statuses,
    active_statuses,
    dismissed_statuses,
    ext_or_higher_statuses,
    ext_review_statuses,
    get_review_active_statuses,
    review_statuses,
)
from .utils import (
    get_action_mapping,
)

__all__ = [
    "DETERMINATION_OUTCOMES",
    "DRAFT_STATE",
    "INITIAL_STATE",
    "PHASES",
    "STAGE_CHANGE_ACTIONS",
    "STATUSES",
    "Stage",
    "UserPermissions",
    "WORKFLOWS",
    "accepted_statuses",
    "active_statuses",
    "dismissed_statuses",
    "ext_or_higher_statuses",
    "ext_review_statuses",
    "get_action_mapping",
    "get_review_active_statuses",
    "review_statuses",
]
