from django.conf import settings
from django.utils.translation import gettext as _

from hypha.apply.funds.workflows import constants, permissions, stage

DoubleStageDefinition = [
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
            'stage': stage.Concept,
            'permissions': permissions.applicant_edit_permissions,
        }
    },
    {
        constants.INITIAL_STATE: {
            'transitions': {
                'concept_more_info': _('Request More Information'),
                'concept_internal_review': _('Open Review'),
                'concept_determination': _('Ready For Preliminary Determination'),
                'invited_to_proposal': _('Invite to Proposal'),
                'concept_rejected': _('Dismiss'),
            },
            'display': _('Need screening'),
            'public': _('Concept Note Received'),
            'stage': stage.Concept,
            'permissions': permissions.default_permissions,
        },
        'concept_more_info': {
            'transitions': {
                constants.INITIAL_STATE: {
                    'display': _('Submit'),
                    'permissions': {permissions.UserPermissions.APPLICANT, permissions.UserPermissions.STAFF, permissions.UserPermissions.LEAD, permissions.UserPermissions.ADMIN},
                    'method': 'create_revision',
                },
                'concept_rejected': _('Dismiss'),
                'invited_to_proposal': _('Invite to Proposal'),
                'concept_determination': _('Ready For Preliminary Determination'),
            },
            'display': _('More information required'),
            'stage': stage.Concept,
            'permissions': permissions.applicant_edit_permissions,
        },
    },
    {
        'concept_internal_review': {
            'transitions': {
                'concept_review_discussion': _('Close Review'),
                constants.INITIAL_STATE: _('Need screening (revert)'),
                'invited_to_proposal': _('Invite to Proposal'),
            },
            'display': _('Internal Review'),
            'public': _('{org_short_name} Review').format(org_short_name=settings.ORG_SHORT_NAME),
            'stage': stage.Concept,
            'permissions': permissions.default_permissions,
        },
    },
    {
        'concept_review_discussion': {
            'transitions': {
                'concept_review_more_info': _('Request More Information'),
                'concept_determination': _('Ready For Preliminary Determination'),
                'concept_internal_review': _('Open Review (revert)'),
                'invited_to_proposal': _('Invite to Proposal'),
                'concept_rejected': _('Dismiss'),
            },
            'display': _('Ready For Discussion'),
            'stage': stage.Concept,
            'permissions': permissions.hidden_from_applicant_permissions,
        },
        'concept_review_more_info': {
            'transitions': {
                'concept_review_discussion': {
                    'display': _('Submit'),
                    'permissions': {permissions.UserPermissions.APPLICANT, permissions.UserPermissions.STAFF, permissions.UserPermissions.LEAD, permissions.UserPermissions.ADMIN},
                    'method': 'create_revision',
                },
                'invited_to_proposal': _('Invite to Proposal'),
            },
            'display': _('More information required'),
            'stage': stage.Concept,
            'permissions': permissions.applicant_edit_permissions,
        },
    },
    {
        'concept_determination': {
            'transitions': {
                'concept_review_discussion': _('Ready For Discussion (revert)'),
                'invited_to_proposal': _('Invite to Proposal'),
                'concept_rejected': _('Dismiss'),
            },
            'display': _('Ready for Preliminary Determination'),
            'permissions': permissions.hidden_from_applicant_permissions,
            'stage': stage.Concept,
        },
    },
    {
        'invited_to_proposal': {
            'display': _('Concept Accepted'),
            'future': _('Preliminary Determination'),
            'transitions': {
                'draft_proposal': {
                    'display': _('Progress'),
                    'method': 'progress_application',
                    'permissions': {permissions.UserPermissions.STAFF, permissions.UserPermissions.LEAD, permissions.UserPermissions.ADMIN},
                    'conditions': 'not_progressed',
                },
            },
            'stage': stage.Concept,
            'permissions': permissions.no_permissions,
        },
        'concept_rejected': {
            'display': _('Dismissed'),
            'stage': stage.Concept,
            'permissions': permissions.no_permissions,
        },
    },
    {
        'draft_proposal': {
            'transitions': {
                'proposal_discussion': {'display': _('Submit'), 'permissions': {permissions.UserPermissions.APPLICANT}, 'method': 'create_revision'},
                'external_review': _('Open External Review'),
                'proposal_determination': _('Ready For Final Determination'),
                'proposal_rejected': _('Dismiss'),
            },
            'display': _('Invited for Proposal'),
            'stage': stage.Proposal,
            'permissions': permissions.applicant_edit_permissions,
        },
    },
    {
        'proposal_discussion': {
            'transitions': {
                'proposal_more_info': _('Request More Information'),
                'proposal_internal_review': _('Open Review'),
                'external_review': _('Open External Review'),
                'proposal_determination': _('Ready For Final Determination'),
                'proposal_rejected': _('Dismiss'),
            },
            'display': _('Proposal Received'),
            'stage': stage.Proposal,
            'permissions': permissions.default_permissions,
        },
        'proposal_more_info': {
            'transitions': {
                'proposal_discussion': {
                    'display': _('Submit'),
                    'permissions': {permissions.UserPermissions.APPLICANT, permissions.UserPermissions.STAFF, permissions.UserPermissions.LEAD, permissions.UserPermissions.ADMIN},
                    'method': 'create_revision',
                },
                'external_review': _('Open External Review'),
                'proposal_determination': _('Ready For Final Determination'),
                'proposal_rejected': _('Dismiss'),
            },
            'display': _('More information required'),
            'stage': stage.Proposal,
            'permissions': permissions.applicant_edit_permissions,
        },
    },
    {
        'proposal_internal_review': {
            'transitions': {
                'post_proposal_review_discussion': _('Close Review'),
                'proposal_discussion': _('Proposal Received (revert)'),
            },
            'display': _('Internal Review'),
            'public': _('{org_short_name} Review').format(org_short_name=settings.ORG_SHORT_NAME),
            'stage': stage.Proposal,
            'permissions': permissions.default_permissions,
        },
    },
    {
        'post_proposal_review_discussion': {
            'transitions': {
                'post_proposal_review_more_info': _('Request More Information'),
                'external_review': _('Open External Review'),
                'proposal_determination': _('Ready For Final Determination'),
                'proposal_internal_review': _('Open Internal Review (revert)'),
                'proposal_rejected': _('Dismiss'),
            },
            'display': _('Ready For Discussion'),
            'stage': stage.Proposal,
            'permissions': permissions.hidden_from_applicant_permissions,
        },
        'post_proposal_review_more_info': {
            'transitions': {
                'post_proposal_review_discussion': {
                    'display': _('Submit'),
                    'permissions': {permissions.UserPermissions.APPLICANT, permissions.UserPermissions.STAFF, permissions.UserPermissions.LEAD, permissions.UserPermissions.ADMIN},
                    'method': 'create_revision',
                },
                'external_review': _('Open External Review'),
            },
            'display': _('More information required'),
            'stage': stage.Proposal,
            'permissions': permissions.applicant_edit_permissions,
        },
    },
    {
        'external_review': {
            'transitions': {
                'post_external_review_discussion': _('Close Review'),
                'post_proposal_review_discussion': _('Ready For Discussion (revert)'),
            },
            'display': _('External Review'),
            'stage': stage.Proposal,
            'permissions': permissions.reviewer_review_permissions,
        },
    },
    {
        'post_external_review_discussion': {
            'transitions': {
                'post_external_review_more_info': _('Request More Information'),
                'proposal_determination': _('Ready For Final Determination'),
                'external_review': _('Open External Review (revert)'),
                'proposal_almost': _('Accept but additional info required'),
                'proposal_accepted': _('Accept'),
                'proposal_rejected': _('Dismiss'),
            },
            'display': _('Ready For Discussion'),
            'stage': stage.Proposal,
            'permissions': permissions.hidden_from_applicant_permissions,
        },
        'post_external_review_more_info': {
            'transitions': {
                'post_external_review_discussion': {
                    'display': _('Submit'),
                    'permissions': {permissions.UserPermissions.APPLICANT, permissions.UserPermissions.STAFF, permissions.UserPermissions.LEAD, permissions.UserPermissions.ADMIN},
                    'method': 'create_revision',
                },
            },
            'display': _('More information required'),
            'stage': stage.Proposal,
            'permissions': permissions.applicant_edit_permissions,
        },
    },
    {
        'proposal_determination': {
            'transitions': {
                'post_external_review_discussion': _('Ready For Discussion (revert)'),
                'proposal_almost': _('Accept but additional info required'),
                'proposal_accepted': _('Accept'),
                'proposal_rejected': _('Dismiss'),
            },
            'display': _('Ready for Final Determination'),
            'permissions': permissions.hidden_from_applicant_permissions,
            'stage': stage.Proposal,
        },
    },
    {
        'proposal_accepted': {
            'display': _('Accepted'),
            'future': _('Final Determination'),
            'stage': stage.Proposal,
            'permissions': permissions.staff_edit_permissions,
        },
        'proposal_almost': {
            'transitions': {
                'proposal_accepted': _('Accept'),
                'post_external_review_discussion': _('Ready For Discussion (revert)'),
            },
            'display': _('Accepted but additional info required'),
            'stage': stage.Proposal,
            'permissions': permissions.applicant_edit_permissions,
        },
        'proposal_rejected': {
            'display': _('Dismissed'),
            'stage': stage.Proposal,
            'permissions': permissions.no_permissions,
        },
    },
]

