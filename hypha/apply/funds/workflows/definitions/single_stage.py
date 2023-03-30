from django.conf import settings
from django.utils.translation import gettext as _

from hypha.apply.funds.workflows import constants, permissions, stage

SingleStageDefinition = [
    {
        constants.DRAFT_STATE: {
            'transitions': {
                constants.INITIAL_STATE: {
                    'display': _('Submit'),
                    'permissions': {permissions.UserPermissions.APPLICANT},
                    'method': 'create_revision',
                },
            },
            'display': _('Draft'),
            'stage': stage.Request,
            'permissions': permissions.applicant_edit_permissions,
        }
    },
    {
        constants.INITIAL_STATE: {
            'transitions': {
                'more_info': _('Request More Information'),
                'internal_review': _('Open Review'),
                'determination': _('Ready For Determination'),
                'almost': _('Accept but additional info required'),
                'accepted': _('Accept'),
                'rejected': _('Dismiss'),
            },
            'display': _('Need screening'),
            'public': _('Application Received'),
            'stage': stage.Request,
            'permissions': permissions.default_permissions,
        },
        'more_info': {
            'transitions': {
                constants.INITIAL_STATE: {
                    'display': _('Submit'),
                    'permissions': {permissions.UserPermissions.APPLICANT, permissions.UserPermissions.STAFF, permissions.UserPermissions.LEAD, permissions.UserPermissions.ADMIN},
                    'method': 'create_revision',
                },
                'determination': _('Ready For Determination'),
                'almost': _('Accept but additional info required'),
                'accepted': _('Accept'),
                'rejected': _('Dismiss'),
            },
            'display': _('More information required'),
            'stage': stage.Request,
            'permissions': permissions.applicant_edit_permissions,
        },
    },
    {
        'internal_review': {
            'transitions': {
                'post_review_discussion': _('Close Review'),
                constants.INITIAL_STATE: _('Need screening (revert)'),
            },
            'display': _('Internal Review'),
            'public': _('{org_short_name} Review').format(org_short_name=settings.ORG_SHORT_NAME),
            'stage': stage.Request,
            'permissions': permissions.default_permissions,
        },
    },
    {
        'post_review_discussion': {
            'transitions': {
                'post_review_more_info': _('Request More Information'),
                'determination': _('Ready For Determination'),
                'internal_review': _('Open Review (revert)'),
                'almost': _('Accept but additional info required'),
                'accepted': _('Accept'),
                'rejected': _('Dismiss'),
            },
            'display': _('Ready For Discussion'),
            'stage': stage.Request,
            'permissions': permissions.hidden_from_applicant_permissions,
        },
        'post_review_more_info': {
            'transitions': {
                'post_review_discussion': {
                    'display': _('Submit'),
                    'permissions': {permissions.UserPermissions.APPLICANT, permissions.UserPermissions.STAFF, permissions.UserPermissions.LEAD, permissions.UserPermissions.ADMIN},
                    'method': 'create_revision',
                },
                'determination': _('Ready For Determination'),
                'almost': _('Accept but additional info required'),
                'accepted': _('Accept'),
                'rejected': _('Dismiss'),
            },
            'display': _('More information required'),
            'stage': stage.Request,
            'permissions': permissions.applicant_edit_permissions,
        },
    },
    {
        'determination': {
            'transitions': {
                'post_review_discussion': _('Ready For Discussion (revert)'),
                'almost': _('Accept but additional info required'),
                'accepted': _('Accept'),
                'rejected': _('Dismiss'),
            },
            'display': _('Ready for Determination'),
            'permissions': permissions.hidden_from_applicant_permissions,
            'stage': stage.Request,
        },
    },
    {
        'accepted': {
            'display': _('Accepted'),
            'future': _('Application Outcome'),
            'stage': stage.Request,
            'permissions': permissions.staff_edit_permissions,
        },
        'almost': {
            'transitions': {
                'accepted': _('Accept'),
                'post_review_discussion': _('Ready For Discussion (revert)'),
            },
            'display': _('Accepted but additional info required'),
            'stage': stage.Request,
            'permissions': permissions.applicant_edit_permissions,
        },
        'rejected': {
            'display': _('Dismissed'),
            'stage': stage.Request,
            'permissions': permissions.no_permissions,
        },
    },
]
