from enum import Enum

from django.utils.translation import gettext as _

from .utils import (
    get_determination_transitions,
    get_stage_change_actions,
    phases_matching,
)

DRAFT_STATE = "draft"
INITIAL_STATE = "in_discussion"

PHASE_BG_COLORS = {
    "Draft": "bg-gray-200",
    "Accepted": "bg-green-200",
    "Need screening": "bg-cyan-200",
    "Ready for Determination": "bg-blue-200",
    "Ready For Discussion": "bg-blue-100",
    "Invited for Proposal": "bg-green-100",
    "Internal Review": "bg-yellow-200",
    "External Review": "bg-yellow-200",
    "More information required": "bg-yellow-100",
    "Accepted but additional info required": "bg-green-100",
    "Dismissed": "bg-rose-200",
}


class UserPermissions(Enum):
    STAFF = 1
    ADMIN = 2
    LEAD = 3
    APPLICANT = 4


STAGE_CHANGE_ACTIONS = get_stage_change_actions()

DETERMINATION_RESPONSE_PHASES = [
    "post_review_discussion",
    "concept_review_discussion",
    "same_post_review_discussion",
    "post_external_review_discussion",
    "ext_post_external_review_discussion",
    "com_post_external_review_discussion",
]

DETERMINATION_OUTCOMES = get_determination_transitions()

OPEN_CALL_PHASES = [
    "com_open_call",
]

COMMUNITY_REVIEW_PHASES = [
    "com_community_review",
]

PHASES_MAPPING = {
    "received": {
        "name": _("Received"),
        "statuses": [INITIAL_STATE, "proposal_discussion"],
    },
    "internal-review": {
        "name": _("Internal Review"),
        "statuses": phases_matching("internal_review"),
    },
    "in-discussion": {
        "name": _("Ready for Discussion"),
        "statuses": phases_matching(
            "discussion", exclude=[INITIAL_STATE, "proposal_discussion"]
        ),
    },
    "more-information": {
        "name": _("More Information Requested"),
        "statuses": phases_matching("more_info"),
    },
    "invited-for-proposal": {
        "name": _("Invited for Proposal"),
        "statuses": ["draft_proposal"],
    },
    "external-review": {
        "name": _("External Review"),
        "statuses": phases_matching("external_review"),
    },
    "ready-for-determination": {
        "name": _("Ready for Determination"),
        "statuses": phases_matching("determination"),
    },
    "accepted": {
        "name": _("Accepted"),
        "statuses": phases_matching("accepted"),
    },
    "dismissed": {
        "name": _("Dismissed"),
        "statuses": phases_matching("rejected"),
    },
}
