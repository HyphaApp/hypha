from django.conf import settings
from django.utils.translation import gettext as _

from ..constants import DRAFT_STATE, INITIAL_STATE, UserPermissions
from ..models.stage import Concept, Proposal
from ..permissions import (
    applicant_edit_permissions,
    default_permissions,
    hidden_from_applicant_permissions,
    no_permissions,
    reviewer_review_permissions,
    staff_edit_permissions,
)

DoubleStageDefinition = [
    {
        DRAFT_STATE: {
            "transitions": {
                INITIAL_STATE: {
                    "display": _("Submit"),
                    "permissions": {UserPermissions.APPLICANT},
                    "method": "create_revision",
                    "custom": {"trigger_on_submit": True},
                },
            },
            "display": _("Draft"),
            "stage": Concept,
            "permissions": applicant_edit_permissions,
        }
    },
    {
        INITIAL_STATE: {
            "transitions": {
                "concept_more_info": _("Request More Information"),
                "concept_internal_review": _("Open Review"),
                "concept_determination": _("Ready For Preliminary Determination"),
                "invited_to_proposal": _("Invite to Proposal"),
                "concept_rejected": _("Dismiss"),
            },
            "display": _("Need screening"),
            "public": _("Concept Note Received"),
            "stage": Concept,
            "permissions": default_permissions,
        },
        "concept_more_info": {
            "transitions": {
                INITIAL_STATE: {
                    "display": _("Submit"),
                    "permissions": {
                        UserPermissions.APPLICANT,
                        UserPermissions.STAFF,
                        UserPermissions.LEAD,
                        UserPermissions.ADMIN,
                    },
                    "method": "create_revision",
                    "custom": {"trigger_on_submit": True},
                },
                "concept_rejected": _("Dismiss"),
                "invited_to_proposal": _("Invite to Proposal"),
                "concept_determination": _("Ready For Preliminary Determination"),
            },
            "display": _("More information required"),
            "stage": Concept,
            "permissions": applicant_edit_permissions,
        },
    },
    {
        "concept_internal_review": {
            "transitions": {
                "concept_review_discussion": _("Close Review"),
                INITIAL_STATE: _("Need screening (revert)"),
                "invited_to_proposal": _("Invite to Proposal"),
            },
            "display": _("Internal Review"),
            "public": _("{ORG_SHORT_NAME} Review").format(
                ORG_SHORT_NAME=settings.ORG_SHORT_NAME
            ),
            "stage": Concept,
            "permissions": default_permissions,
        },
    },
    {
        "concept_review_discussion": {
            "transitions": {
                "concept_review_more_info": _("Request More Information"),
                "concept_determination": _("Ready For Preliminary Determination"),
                "concept_internal_review": _("Open Review (revert)"),
                "invited_to_proposal": _("Invite to Proposal"),
                "concept_rejected": _("Dismiss"),
            },
            "display": _("Ready For Discussion"),
            "stage": Concept,
            "permissions": hidden_from_applicant_permissions,
        },
        "concept_review_more_info": {
            "transitions": {
                "concept_review_discussion": {
                    "display": _("Submit"),
                    "permissions": {
                        UserPermissions.APPLICANT,
                        UserPermissions.STAFF,
                        UserPermissions.LEAD,
                        UserPermissions.ADMIN,
                    },
                    "method": "create_revision",
                    "custom": {"trigger_on_submit": True},
                },
                "invited_to_proposal": _("Invite to Proposal"),
            },
            "display": _("More information required"),
            "stage": Concept,
            "permissions": applicant_edit_permissions,
        },
    },
    {
        "concept_determination": {
            "transitions": {
                "concept_review_discussion": _("Ready For Discussion (revert)"),
                "invited_to_proposal": _("Invite to Proposal"),
                "concept_rejected": _("Dismiss"),
            },
            "display": _("Ready for Preliminary Determination"),
            "permissions": hidden_from_applicant_permissions,
            "stage": Concept,
        },
    },
    {
        "invited_to_proposal": {
            "display": _("Concept Accepted"),
            "future": _("Preliminary Determination"),
            "transitions": {
                "draft_proposal": {
                    "display": _("Progress"),
                    "method": "progress_application",
                    "permissions": {
                        UserPermissions.STAFF,
                        UserPermissions.LEAD,
                        UserPermissions.ADMIN,
                    },
                    "conditions": "not_progressed",
                },
            },
            "stage": Concept,
            "permissions": no_permissions,
        },
        "concept_rejected": {
            "display": _("Dismissed"),
            "stage": Concept,
            "permissions": no_permissions,
        },
    },
    {
        "draft_proposal": {
            "transitions": {
                "proposal_discussion": {
                    "display": _("Submit"),
                    "permissions": {UserPermissions.APPLICANT},
                    "method": "create_revision",
                    "custom": {"trigger_on_submit": True},
                },
                "external_review": _("Open External Review"),
                "proposal_determination": _("Ready For Final Determination"),
                "proposal_rejected": _("Dismiss"),
            },
            "display": _("Invited for Proposal"),
            "stage": Proposal,
            "permissions": applicant_edit_permissions,
        },
    },
    {
        "proposal_discussion": {
            "transitions": {
                "proposal_more_info": _("Request More Information"),
                "proposal_internal_review": _("Open Review"),
                "external_review": _("Open External Review"),
                "proposal_determination": _("Ready For Final Determination"),
                "proposal_rejected": _("Dismiss"),
            },
            "display": _("Proposal Received"),
            "stage": Proposal,
            "permissions": default_permissions,
        },
        "proposal_more_info": {
            "transitions": {
                "proposal_discussion": {
                    "display": _("Submit"),
                    "permissions": {
                        UserPermissions.APPLICANT,
                        UserPermissions.STAFF,
                        UserPermissions.LEAD,
                        UserPermissions.ADMIN,
                    },
                    "method": "create_revision",
                    "custom": {"trigger_on_submit": True},
                },
                "external_review": _("Open External Review"),
                "proposal_determination": _("Ready For Final Determination"),
                "proposal_rejected": _("Dismiss"),
            },
            "display": _("More information required"),
            "stage": Proposal,
            "permissions": applicant_edit_permissions,
        },
    },
    {
        "proposal_internal_review": {
            "transitions": {
                "post_proposal_review_discussion": _("Close Review"),
                "proposal_discussion": _("Proposal Received (revert)"),
            },
            "display": _("Internal Review"),
            "public": _("{ORG_SHORT_NAME} Review").format(
                ORG_SHORT_NAME=settings.ORG_SHORT_NAME
            ),
            "stage": Proposal,
            "permissions": default_permissions,
        },
    },
    {
        "post_proposal_review_discussion": {
            "transitions": {
                "post_proposal_review_more_info": _("Request More Information"),
                "external_review": _("Open External Review"),
                "proposal_determination": _("Ready For Final Determination"),
                "proposal_internal_review": _("Open Internal Review (revert)"),
                "proposal_rejected": _("Dismiss"),
            },
            "display": _("Ready For Discussion"),
            "stage": Proposal,
            "permissions": hidden_from_applicant_permissions,
        },
        "post_proposal_review_more_info": {
            "transitions": {
                "post_proposal_review_discussion": {
                    "display": _("Submit"),
                    "permissions": {
                        UserPermissions.APPLICANT,
                        UserPermissions.STAFF,
                        UserPermissions.LEAD,
                        UserPermissions.ADMIN,
                    },
                    "method": "create_revision",
                    "custom": {"trigger_on_submit": True},
                },
                "external_review": _("Open External Review"),
            },
            "display": _("More information required"),
            "stage": Proposal,
            "permissions": applicant_edit_permissions,
        },
    },
    {
        "external_review": {
            "transitions": {
                "post_external_review_discussion": _("Close Review"),
                "post_proposal_review_discussion": _("Ready For Discussion (revert)"),
            },
            "display": _("External Review"),
            "stage": Proposal,
            "permissions": reviewer_review_permissions,
        },
    },
    {
        "post_external_review_discussion": {
            "transitions": {
                "post_external_review_more_info": _("Request More Information"),
                "proposal_determination": _("Ready For Final Determination"),
                "external_review": _("Open External Review (revert)"),
                "proposal_almost": _("Accept but additional info required"),
                "proposal_accepted": _("Accept"),
                "proposal_rejected": _("Dismiss"),
            },
            "display": _("Ready For Discussion"),
            "stage": Proposal,
            "permissions": hidden_from_applicant_permissions,
        },
        "post_external_review_more_info": {
            "transitions": {
                "post_external_review_discussion": {
                    "display": _("Submit"),
                    "permissions": {
                        UserPermissions.APPLICANT,
                        UserPermissions.STAFF,
                        UserPermissions.LEAD,
                        UserPermissions.ADMIN,
                    },
                    "method": "create_revision",
                    "custom": {"trigger_on_submit": True},
                },
            },
            "display": _("More information required"),
            "stage": Proposal,
            "permissions": applicant_edit_permissions,
        },
    },
    {
        "proposal_determination": {
            "transitions": {
                "post_external_review_discussion": _("Ready For Discussion (revert)"),
                "proposal_almost": _("Accept but additional info required"),
                "proposal_accepted": _("Accept"),
                "proposal_rejected": _("Dismiss"),
            },
            "display": _("Ready for Final Determination"),
            "permissions": hidden_from_applicant_permissions,
            "stage": Proposal,
        },
    },
    {
        "proposal_accepted": {
            "display": _("Accepted"),
            "future": _("Final Determination"),
            "stage": Proposal,
            "permissions": staff_edit_permissions,
        },
        "proposal_almost": {
            "transitions": {
                "proposal_accepted": _("Accept"),
                "post_external_review_discussion": _("Ready For Discussion (revert)"),
            },
            "display": _("Accepted but additional info required"),
            "stage": Proposal,
            "permissions": applicant_edit_permissions,
        },
        "proposal_rejected": {
            "display": _("Dismissed"),
            "stage": Proposal,
            "permissions": no_permissions,
        },
    },
]
