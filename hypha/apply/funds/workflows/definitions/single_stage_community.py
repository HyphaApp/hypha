from django.conf import settings
from django.utils.translation import gettext as _

from hypha.apply.funds.workflows import constants, permissions, stage

SingleStageCommunityDefinition = [
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
            'stage': stage.RequestCom,
            'permissions': permissions.applicant_edit_permissions,
        }
    },
    {
        constants.INITIAL_STATE: {
            'transitions': {
                'com_more_info': _('Request More Information'),
                'com_open_call': 'Open Call (public)',
                'com_internal_review': _('Open Review'),
                'com_community_review': _('Open Community Review'),
                'com_determination': _('Ready For Determination'),
                'com_rejected': _('Dismiss'),
            },
            'display': _('Need screening'),
            'public': _('Application Received'),
            'stage': stage.RequestCom,
            'permissions': permissions.default_permissions,
        },
        'com_more_info': {
            'transitions': {
                constants.INITIAL_STATE: {
                    'display': _('Submit'),
                    'permissions': {permissions.UserPermissions.APPLICANT, permissions.UserPermissions.STAFF, permissions.UserPermissions.LEAD, permissions.UserPermissions.ADMIN},
                    'method': 'create_revision',
                },
            },
            'display': _('More information required'),
            'stage': stage.RequestCom,
            'permissions': permissions.applicant_edit_permissions,
        },
        'com_open_call': {
            'transitions': {
                constants.INITIAL_STATE: _('Need screening (revert)'),
                'com_rejected': _('Dismiss'),
            },
            'display': 'Open Call (public)',
            'stage': stage.RequestCom,
            'permissions': permissions.staff_edit_permissions,
        },
    },
    {
        'com_internal_review': {
            'transitions': {
                'com_community_review': _('Open Community Review'),
                'com_post_review_discussion': _('Close Review'),
                constants.INITIAL_STATE: _('Need screening (revert)'),
                'com_rejected': _('Dismiss'),
            },
            'display': _('Internal Review'),
            'public': _('{org_short_name} Review').format(org_short_name=settings.ORG_SHORT_NAME),
            'stage': stage.RequestCom,
            'permissions': permissions.default_permissions,
        },
        'com_community_review': {
            'transitions': {
                'com_post_review_discussion': _('Close Review'),
                'com_internal_review': _('Open Internal Review (revert)'),
                'com_rejected': _('Dismiss'),
            },
            'display': _('Community Review'),
            'public': _('{org_short_name} Review').format(org_short_name=settings.ORG_SHORT_NAME),
            'stage': stage.RequestCom,
            'permissions': permissions.community_review_permissions,
        },
    },
    {
        'com_post_review_discussion': {
            'transitions': {
                'com_post_review_more_info': _('Request More Information'),
                'com_external_review': _('Open External Review'),
                'com_determination': _('Ready For Determination'),
                'com_internal_review': _('Open Internal Review (revert)'),
                'com_rejected': _('Dismiss'),
            },
            'display': _('Ready For Discussion'),
            'stage': stage.RequestCom,
            'permissions': permissions.hidden_from_applicant_permissions,
        },
        'com_post_review_more_info': {
            'transitions': {
                'com_post_review_discussion': {
                    'display': _('Submit'),
                    'permissions': {permissions.UserPermissions.APPLICANT, permissions.UserPermissions.STAFF, permissions.UserPermissions.LEAD, permissions.UserPermissions.ADMIN},
                    'method': 'create_revision',
                },
            },
            'display': _('More information required'),
            'stage': stage.RequestCom,
            'permissions': permissions.applicant_edit_permissions,
        },
    },
    {
        'com_external_review': {
            'transitions': {
                'com_post_external_review_discussion': _('Close Review'),
                'com_post_review_discussion': _('Ready For Discussion (revert)'),
            },
            'display': _('External Review'),
            'stage': stage.RequestCom,
            'permissions': permissions.reviewer_review_permissions,
        },
    },
    {
        'com_post_external_review_discussion': {
            'transitions': {
                'com_post_external_review_more_info': _('Request More Information'),
                'com_determination': _('Ready For Determination'),
                'com_external_review': _('Open External Review (revert)'),
                'com_almost': _('Accept but additional info required'),
                'com_accepted': _('Accept'),
                'com_rejected': _('Dismiss'),
            },
            'display': _('Ready For Discussion'),
            'stage': stage.RequestCom,
            'permissions': permissions.hidden_from_applicant_permissions,
        },
        'com_post_external_review_more_info': {
            'transitions': {
                'com_post_external_review_discussion': {
                    'display': _('Submit'),
                    'permissions': {permissions.UserPermissions.APPLICANT, permissions.UserPermissions.STAFF, permissions.UserPermissions.LEAD, permissions.UserPermissions.ADMIN},
                    'method': 'create_revision',
                },
            },
            'display': _('More information required'),
            'stage': stage.RequestCom,
            'permissions': permissions.applicant_edit_permissions,
        },
    },
    {
        'com_determination': {
            'transitions': {
                'com_post_external_review_discussion': _('Ready For Discussion (revert)'),
                'com_almost': _('Accept but additional info required'),
                'com_accepted': _('Accept'),
                'com_rejected': _('Dismiss'),
            },
            'display': _('Ready for Determination'),
            'permissions': permissions.hidden_from_applicant_permissions,
            'stage': stage.RequestCom,
        },
    },
    {
        'com_accepted': {
            'display': _('Accepted'),
            'future': _('Application Outcome'),
            'stage': stage.RequestCom,
            'permissions': permissions.staff_edit_permissions,
        },
        'com_almost': {
            'transitions': {
                'com_accepted': _('Accept'),
                'com_post_external_review_discussion': _('Ready For Discussion (revert)'),
            },
            'display': _('Accepted but additional info required'),
            'stage': stage.RequestCom,
            'permissions': permissions.applicant_edit_permissions,
        },
        'com_rejected': {
            'display': _('Dismissed'),
            'stage': stage.RequestCom,
            'permissions': permissions.no_permissions,
        },
    },
]
