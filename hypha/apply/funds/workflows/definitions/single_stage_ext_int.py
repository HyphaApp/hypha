from django.conf import settings
from django.utils.translation import gettext_lazy as _

from ..constants import DRAFT_STATE, INITIAL_STATE, UserPermissions
from ..models.stage import RequestExtInt
from ..permissions import (
    applicant_edit_permissions,
    default_permissions,
    hidden_from_applicant_permissions,
    no_permissions,
    reviewer_review_permissions,
    staff_edit_permissions,
)

SingleStageExtIntDefinition = [
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
            "stage": RequestExtInt,
            "permissions": applicant_edit_permissions,
        }
    },
    {
        INITIAL_STATE: {
            "transitions": {
                "ext_int_more_info": _("Request More Information"),
                "ext_int_external_review": _("Open External Review"),
                "ext_int_determination": _("Ready For Determination"),
                "ext_int_rejected": _("Dismiss"),
            },
            "display": _("Need screening"),
            "public": _("Application Received"),
            "stage": RequestExtInt,
            "permissions": default_permissions,
        },
        "ext_int_more_info": {
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
            "stage": RequestExtInt,
            "permissions": applicant_edit_permissions,
        },
    },
    {
        "ext_int_external_review": {
            "transitions": {
                "ext_int_post_external_review_discussion": _("Close Review"),
                INITIAL_STATE: _("Need screening (revert)"),
            },
            "display": _("External Review"),
            "stage": RequestExtInt,
            "permissions": reviewer_review_permissions,
        },
    },
    {
        "ext_int_post_external_review_discussion": {
            "transitions": {
                "ext_int_post_external_review_more_info": _("Request More Information"),
                "ext_int_internal_review": _("Open Internal Review"),
                "ext_int_determination": _("Ready For Determination"),
                "ext_int_external_review": _("Open External Review (revert)"),
                "ext_int_rejected": _("Dismiss"),
            },
            "display": _("Ready For Discussion"),
            "stage": RequestExtInt,
            "permissions": hidden_from_applicant_permissions,
        },
        "ext_int_post_external_review_more_info": {
            "transitions": {
                "ext_int_post_external_review_discussion": {
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
            "stage": RequestExtInt,
            "permissions": applicant_edit_permissions,
        },
    },
    {
        "ext_int_internal_review": {
            "transitions": {
                "ext_int_post_review_discussion": _("Close Review"),
                "ext_int_post_external_review_discussion": _(
                    "Ready For Discussion (revert)"
                ),
            },
            "display": _("Internal Review"),
            "public": _("{ORG_SHORT_NAME} Review").format(
                ORG_SHORT_NAME=settings.ORG_SHORT_NAME
            ),
            "stage": RequestExtInt,
            "permissions": default_permissions,
        },
    },
    {
        "ext_int_post_review_discussion": {
            "transitions": {
                "ext_int_post_review_more_info": _("Request More Information"),
                "ext_int_determination": _("Ready For Determination"),
                "ext_int_internal_review": _("Open Internal Review (revert)"),
                "ext_int_accepted": _("Accept"),
                "ext_int_waitlisted": _("Waitlist"),
                "ext_int_rejected": _("Dismiss"),
            },
            "display": _("Ready For Discussion"),
            "stage": RequestExtInt,
            "permissions": hidden_from_applicant_permissions,
        },
        "ext_int_post_review_more_info": {
            "transitions": {
                "ext_int_post_review_discussion": {
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
            "stage": RequestExtInt,
            "permissions": applicant_edit_permissions,
        },
    },
    {
        "ext_int_determination": {
            "transitions": {
                "ext_int_post_review_discussion": _("Ready For Discussion (revert)"),
                "ext_int_accepted": _("Accept"),
                "ext_int_waitlisted": _("Waitlist"),
                "ext_int_rejected": _("Dismiss"),
            },
            "display": _("Ready for Determination"),
            "permissions": hidden_from_applicant_permissions,
            "stage": RequestExtInt,
        },
    },
    {
        "ext_int_accepted": {
            "display": _("Accepted"),
            "future": _("Application Outcome"),
            "stage": RequestExtInt,
            "permissions": staff_edit_permissions,
        },
        "ext_int_waitlisted": {
            "transitions": {
                "ext_int_accepted": _("Accept"),
                "ext_int_rejected": _("Dismiss"),
                "ext_int_determination": _("Ready for Determination (revert)"),
            },
            "display": _("Waitlisted"),
            "stage": RequestExtInt,
            "permissions": staff_edit_permissions,
        },
        "ext_int_rejected": {
            "display": _("Dismissed"),
            "stage": RequestExtInt,
            "permissions": no_permissions,
        },
    },
]
