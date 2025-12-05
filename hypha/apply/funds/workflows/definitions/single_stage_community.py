from django.conf import settings
from django.utils.translation import gettext as _

from ..constants import DRAFT_STATE, INITIAL_STATE, UserPermissions
from ..models.stage import RequestCom
from ..permissions import (
    applicant_edit_permissions,
    community_review_permissions,
    default_permissions,
    hidden_from_applicant_permissions,
    no_permissions,
    reviewer_review_permissions,
    staff_edit_permissions,
)

SingleStageCommunityDefinition = [
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
            "stage": RequestCom,
            "permissions": applicant_edit_permissions,
        }
    },
    {
        INITIAL_STATE: {
            "transitions": {
                "com_more_info": _("Request More Information"),
                "com_open_call": "Open Call (public)",
                "com_internal_review": _("Open Review"),
                "com_community_review": _("Open Community Review"),
                "com_determination": _("Ready For Determination"),
                "com_rejected": _("Dismiss"),
            },
            "display": _("Need screening"),
            "public": _("Application Received"),
            "stage": RequestCom,
            "permissions": default_permissions,
        },
        "com_more_info": {
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
            },
            "display": _("More information required"),
            "stage": RequestCom,
            "permissions": applicant_edit_permissions,
        },
        "com_open_call": {
            "transitions": {
                INITIAL_STATE: _("Need screening (revert)"),
                "com_rejected": _("Dismiss"),
            },
            "display": "Open Call (public)",
            "stage": RequestCom,
            "permissions": staff_edit_permissions,
        },
    },
    {
        "com_internal_review": {
            "transitions": {
                "com_community_review": _("Open Community Review"),
                "com_post_review_discussion": _("Close Review"),
                INITIAL_STATE: _("Need screening (revert)"),
                "com_rejected": _("Dismiss"),
            },
            "display": _("Internal Review"),
            "public": _("{ORG_SHORT_NAME} Review").format(
                ORG_SHORT_NAME=settings.ORG_SHORT_NAME
            ),
            "stage": RequestCom,
            "permissions": default_permissions,
        },
        "com_community_review": {
            "transitions": {
                "com_post_review_discussion": _("Close Review"),
                "com_internal_review": _("Open Internal Review (revert)"),
                "com_rejected": _("Dismiss"),
            },
            "display": _("Community Review"),
            "public": _("{ORG_SHORT_NAME} Review").format(
                ORG_SHORT_NAME=settings.ORG_SHORT_NAME
            ),
            "stage": RequestCom,
            "permissions": community_review_permissions,
        },
    },
    {
        "com_post_review_discussion": {
            "transitions": {
                "com_post_review_more_info": _("Request More Information"),
                "com_external_review": _("Open External Review"),
                "com_determination": _("Ready For Determination"),
                "com_internal_review": _("Open Internal Review (revert)"),
                "com_rejected": _("Dismiss"),
            },
            "display": _("Ready For Discussion"),
            "stage": RequestCom,
            "permissions": hidden_from_applicant_permissions,
        },
        "com_post_review_more_info": {
            "transitions": {
                "com_post_review_discussion": {
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
            "stage": RequestCom,
            "permissions": applicant_edit_permissions,
        },
    },
    {
        "com_external_review": {
            "transitions": {
                "com_post_external_review_discussion": _("Close Review"),
                "com_post_review_discussion": _("Ready For Discussion (revert)"),
            },
            "display": _("External Review"),
            "stage": RequestCom,
            "permissions": reviewer_review_permissions,
        },
    },
    {
        "com_post_external_review_discussion": {
            "transitions": {
                "com_post_external_review_more_info": _("Request More Information"),
                "com_determination": _("Ready For Determination"),
                "com_external_review": _("Open External Review (revert)"),
                "com_almost": _("Accept but additional info required"),
                "com_accepted": _("Accept"),
                "com_rejected": _("Dismiss"),
            },
            "display": _("Ready For Discussion"),
            "stage": RequestCom,
            "permissions": hidden_from_applicant_permissions,
        },
        "com_post_external_review_more_info": {
            "transitions": {
                "com_post_external_review_discussion": {
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
            "stage": RequestCom,
            "permissions": applicant_edit_permissions,
        },
    },
    {
        "com_determination": {
            "transitions": {
                "com_post_external_review_discussion": _(
                    "Ready For Discussion (revert)"
                ),
                "com_almost": _("Accept but additional info required"),
                "com_accepted": _("Accept"),
                "com_rejected": _("Dismiss"),
            },
            "display": _("Ready for Determination"),
            "permissions": hidden_from_applicant_permissions,
            "stage": RequestCom,
        },
    },
    {
        "com_accepted": {
            "display": _("Accepted"),
            "future": _("Application Outcome"),
            "stage": RequestCom,
            "permissions": staff_edit_permissions,
        },
        "com_almost": {
            "transitions": {
                "com_accepted": _("Accept"),
                "com_post_external_review_discussion": _(
                    "Ready For Discussion (revert)"
                ),
            },
            "display": _("Accepted but additional info required"),
            "stage": RequestCom,
            "permissions": applicant_edit_permissions,
        },
        "com_rejected": {
            "display": _("Dismissed"),
            "stage": RequestCom,
            "permissions": no_permissions,
        },
    },
]
