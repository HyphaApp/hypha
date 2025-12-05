from django.conf import settings
from django.utils.translation import gettext as _

from ..constants import DRAFT_STATE, INITIAL_STATE, UserPermissions
from ..models.stage import Request
from ..permissions import (
    applicant_edit_permissions,
    default_permissions,
    hidden_from_applicant_permissions,
    no_permissions,
    staff_edit_permissions,
)

SingleStageDefinition = [
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
            "stage": Request,
            "permissions": applicant_edit_permissions,
        }
    },
    {
        INITIAL_STATE: {
            "transitions": {
                "more_info": _("Request More Information"),
                "internal_review": _("Open Review"),
                "determination": _("Ready For Determination"),
                "almost": _("Accept but additional info required"),
                "accepted": _("Accept"),
                "rejected": _("Dismiss"),
            },
            "display": _("Need screening"),
            "public": _("Application Received"),
            "stage": Request,
            "permissions": default_permissions,
        },
        "more_info": {
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
                "determination": _("Ready For Determination"),
                "almost": _("Accept but additional info required"),
                "accepted": _("Accept"),
                "rejected": _("Dismiss"),
            },
            "display": _("More information required"),
            "stage": Request,
            "permissions": applicant_edit_permissions,
        },
    },
    {
        "internal_review": {
            "transitions": {
                "post_review_discussion": _("Close Review"),
                INITIAL_STATE: _("Need screening (revert)"),
            },
            "display": _("Internal Review"),
            "public": _("{ORG_SHORT_NAME} Review").format(
                ORG_SHORT_NAME=settings.ORG_SHORT_NAME
            ),
            "stage": Request,
            "permissions": default_permissions,
        },
    },
    {
        "post_review_discussion": {
            "transitions": {
                "post_review_more_info": _("Request More Information"),
                "determination": _("Ready For Determination"),
                "internal_review": _("Open Review (revert)"),
                "almost": _("Accept but additional info required"),
                "accepted": _("Accept"),
                "rejected": _("Dismiss"),
            },
            "display": _("Ready For Discussion"),
            "stage": Request,
            "permissions": hidden_from_applicant_permissions,
        },
        "post_review_more_info": {
            "transitions": {
                "post_review_discussion": {
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
                "determination": _("Ready For Determination"),
                "almost": _("Accept but additional info required"),
                "accepted": _("Accept"),
                "rejected": _("Dismiss"),
            },
            "display": _("More information required"),
            "stage": Request,
            "permissions": applicant_edit_permissions,
        },
    },
    {
        "determination": {
            "transitions": {
                "post_review_discussion": _("Ready For Discussion (revert)"),
                "almost": _("Accept but additional info required"),
                "accepted": _("Accept"),
                "rejected": _("Dismiss"),
            },
            "display": _("Ready for Determination"),
            "permissions": hidden_from_applicant_permissions,
            "stage": Request,
        },
    },
    {
        "accepted": {
            "display": _("Accepted"),
            "future": _("Application Outcome"),
            "stage": Request,
            "permissions": staff_edit_permissions,
        },
        "almost": {
            "transitions": {
                "accepted": _("Accept"),
                "post_review_discussion": _("Ready For Discussion (revert)"),
            },
            "display": _("Accepted but additional info required"),
            "stage": Request,
            "permissions": applicant_edit_permissions,
        },
        "rejected": {
            "display": _("Dismissed"),
            "stage": Request,
            "permissions": no_permissions,
        },
    },
]
