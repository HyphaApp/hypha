from django.conf import settings
from django.utils.translation import gettext as _

from ..constants import DRAFT_STATE, INITIAL_STATE, UserPermissions
from ..models.stage import RequestExt
from ..permissions import (
    applicant_edit_permissions,
    default_permissions,
    hidden_from_applicant_permissions,
    no_permissions,
    reviewer_review_permissions,
    staff_edit_permissions,
)

SingleStageExternalDefinition = [
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
            "stage": RequestExt,
            "permissions": applicant_edit_permissions,
        }
    },
    {
        INITIAL_STATE: {
            "transitions": {
                "ext_more_info": _("Request More Information"),
                "ext_internal_review": _("Open Review"),
                "ext_determination": _("Ready For Determination"),
                "ext_rejected": _("Dismiss"),
            },
            "display": _("Need screening"),
            "public": _("Application Received"),
            "stage": RequestExt,
            "permissions": default_permissions,
        },
        "ext_more_info": {
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
            "stage": RequestExt,
            "permissions": applicant_edit_permissions,
        },
    },
    {
        "ext_internal_review": {
            "transitions": {
                "ext_post_review_discussion": _("Close Review"),
                INITIAL_STATE: _("Need screening (revert)"),
            },
            "display": _("Internal Review"),
            "public": _("{org_short_name} Review").format(
                org_short_name=settings.ORG_SHORT_NAME
            ),
            "stage": RequestExt,
            "permissions": default_permissions,
        },
    },
    {
        "ext_post_review_discussion": {
            "transitions": {
                "ext_post_review_more_info": _("Request More Information"),
                "ext_external_review": _("Open External Review"),
                "ext_determination": _("Ready For Determination"),
                "ext_internal_review": _("Open Internal Review (revert)"),
                "ext_rejected": _("Dismiss"),
            },
            "display": _("Ready For Discussion"),
            "stage": RequestExt,
            "permissions": hidden_from_applicant_permissions,
        },
        "ext_post_review_more_info": {
            "transitions": {
                "ext_post_review_discussion": {
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
            "stage": RequestExt,
            "permissions": applicant_edit_permissions,
        },
    },
    {
        "ext_external_review": {
            "transitions": {
                "ext_post_external_review_discussion": _("Close Review"),
                "ext_post_review_discussion": _("Ready For Discussion (revert)"),
            },
            "display": _("External Review"),
            "stage": RequestExt,
            "permissions": reviewer_review_permissions,
        },
    },
    {
        "ext_post_external_review_discussion": {
            "transitions": {
                "ext_post_external_review_more_info": _("Request More Information"),
                "ext_determination": _("Ready For Determination"),
                "ext_external_review": _("Open External Review (revert)"),
                "ext_almost": _("Accept but additional info required"),
                "ext_accepted": _("Accept"),
                "ext_rejected": _("Dismiss"),
            },
            "display": _("Ready For Discussion"),
            "stage": RequestExt,
            "permissions": hidden_from_applicant_permissions,
        },
        "ext_post_external_review_more_info": {
            "transitions": {
                "ext_post_external_review_discussion": {
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
            "stage": RequestExt,
            "permissions": applicant_edit_permissions,
        },
    },
    {
        "ext_determination": {
            "transitions": {
                "ext_post_external_review_discussion": _(
                    "Ready For Discussion (revert)"
                ),
                "ext_almost": _("Accept but additional info required"),
                "ext_accepted": _("Accept"),
                "ext_rejected": _("Dismiss"),
            },
            "display": _("Ready for Determination"),
            "permissions": hidden_from_applicant_permissions,
            "stage": RequestExt,
        },
    },
    {
        "ext_accepted": {
            "display": _("Accepted"),
            "future": _("Application Outcome"),
            "stage": RequestExt,
            "permissions": staff_edit_permissions,
        },
        "ext_almost": {
            "transitions": {
                "ext_accepted": _("Accept"),
                "ext_post_external_review_discussion": _(
                    "Ready For Discussion (revert)"
                ),
            },
            "display": _("Accepted but additional info required"),
            "stage": RequestExt,
            "permissions": applicant_edit_permissions,
        },
        "ext_rejected": {
            "display": _("Dismissed"),
            "stage": RequestExt,
            "permissions": no_permissions,
        },
    },
]
