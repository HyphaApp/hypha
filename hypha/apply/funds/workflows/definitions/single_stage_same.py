from django.conf import settings
from django.utils.translation import gettext as _

from ..constants import DRAFT_STATE, INITIAL_STATE, UserPermissions
from ..models.stage import RequestSame
from ..permissions import (
    applicant_edit_permissions,
    default_permissions,
    hidden_from_applicant_permissions,
    no_permissions,
    reviewer_review_permissions,
    staff_edit_permissions,
)

SingleStageSameDefinition = [
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
            "stage": RequestSame,
            "permissions": applicant_edit_permissions,
        }
    },
    {
        INITIAL_STATE: {
            "transitions": {
                "same_more_info": _("Request More Information"),
                "same_internal_review": _("Open Review"),
                "same_determination": _("Ready For Determination"),
                "same_rejected": _("Dismiss"),
            },
            "display": _("Need screening"),
            "public": _("Application Received"),
            "stage": RequestSame,
            "permissions": default_permissions,
        },
        "same_more_info": {
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
            "stage": RequestSame,
            "permissions": applicant_edit_permissions,
        },
    },
    {
        "same_internal_review": {
            "transitions": {
                "same_post_review_discussion": _("Close Review"),
                INITIAL_STATE: _("Need screening (revert)"),
            },
            "display": _("Review"),
            "public": _("{ORG_SHORT_NAME} Review").format(
                ORG_SHORT_NAME=settings.ORG_SHORT_NAME
            ),
            "stage": RequestSame,
            "permissions": reviewer_review_permissions,
        },
    },
    {
        "same_post_review_discussion": {
            "transitions": {
                "same_post_review_more_info": _("Request More Information"),
                "same_determination": _("Ready For Determination"),
                "same_internal_review": _("Open Review (revert)"),
                "same_rejected": _("Dismiss"),
            },
            "display": _("Ready For Discussion"),
            "stage": RequestSame,
            "permissions": hidden_from_applicant_permissions,
        },
        "same_post_review_more_info": {
            "transitions": {
                "same_post_review_discussion": {
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
            "stage": RequestSame,
            "permissions": applicant_edit_permissions,
        },
    },
    {
        "same_determination": {
            "transitions": {
                "same_post_review_discussion": _("Ready For Discussion (revert)"),
                "same_almost": _("Accept but additional info required"),
                "same_accepted": _("Accept"),
                "same_rejected": _("Dismiss"),
            },
            "display": _("Ready for Determination"),
            "permissions": hidden_from_applicant_permissions,
            "stage": RequestSame,
        },
    },
    {
        "same_accepted": {
            "display": _("Accepted"),
            "future": _("Application Outcome"),
            "stage": RequestSame,
            "permissions": staff_edit_permissions,
        },
        "same_almost": {
            "transitions": {
                "same_accepted": _("Accept"),
                "same_post_review_discussion": _("Ready For Discussion (revert)"),
            },
            "display": _("Accepted but additional info required"),
            "stage": RequestSame,
            "permissions": applicant_edit_permissions,
        },
        "same_rejected": {
            "display": _("Dismissed"),
            "stage": RequestSame,
            "permissions": no_permissions,
        },
    },
]
