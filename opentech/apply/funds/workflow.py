from collections import defaultdict
from enum import Enum
import itertools

from django.conf import settings
from django.utils.text import slugify

"""
This file defines classes which allow you to compose workflows based on the following structure:

Workflow -> Stage -> Phase -> Action

Current limitations:
* Changing the name of a phase will mean that any object which references it cannot progress. [will
be fixed when streamfield, may require intermediate fix prior to launch]
* Do not reorder without looking at workflow automations steps in form_valid() in
opentech/apply/funds/views.py and opentech/apply/review/views.py.
"""


class UserPermissions(Enum):
    STAFF = 1
    ADMIN = 2
    LEAD = 3
    APPLICANT = 4


class Workflow(dict):
    def __init__(self, name, admin_name, **data):
        self.name = name
        self.admin_name = admin_name
        super().__init__(**data)

    def __str__(self):
        return self.name

    @property
    def stages(self):
        stages = []
        for phase in self.values():
            if phase.stage not in stages:
                stages.append(phase.stage)
        return stages

    @property
    def stepped_phases(self):
        phases = defaultdict(list)
        for phase in list(self.values()):
            phases[phase.step].append(phase)
        return phases

    def phases_for(self, user=None):
        # Grab the first phase for each step - visible only, the display phase
        return [
            phase for phase, *_ in self.stepped_phases.values()
            if not user or phase.permissions.can_view(user)
        ]

    def previous_visible(self, current, user):
        """Find the latest phase that the user has view permissions for"""
        display_phase = self.stepped_phases[current.step][0]
        phases = self.phases_for()
        index = phases.index(display_phase)
        for phase in phases[index - 1::-1]:
            if phase.permissions.can_view(user):
                return phase


class Phase:
    """
    Phase Names:
    display_name = phase name displayed to staff members in the system
    public_name = phase name displayed to applicants in the system
    future_name = phase_name displayed to applicants if they haven't passed this stage
    """

    def __init__(self, name, display, stage, permissions, step, public=None, future=None, transitions=dict()):
        self.name = name
        self.display_name = display
        if public and future:
            raise ValueError("Cant provide both a future and a public name")

        self.public_name = public or self.display_name
        self.future_name_staff = future or self.display_name
        self.future_name_public = future or self.public_name
        self.stage = stage
        self.permissions = Permissions(permissions)
        self.step = step

        # For building transition methods on the parent
        self.transitions = {}

        default_permissions = {UserPermissions.STAFF, UserPermissions.LEAD, UserPermissions.ADMIN}

        for transition_target, action in transitions.items():
            transition = dict()
            try:
                transition['display'] = action.get('display')
            except AttributeError:
                transition['display'] = action
                transition['permissions'] = default_permissions
            else:
                transition['method'] = action.get('method')
                conditions = action.get('conditions', '')
                transition['conditions'] = conditions.split(',') if conditions else []
                transition['permissions'] = action.get('permissions', default_permissions)
            self.transitions[transition_target] = transition

    def __str__(self):
        return self.display_name

    def __repr__(self):
        return f'<Phase: {self.display_name} ({self.public_name})>'


class Stage:
    def __init__(self, name, has_external_review=False):
        self.name = name
        self.has_external_review = has_external_review

    def __str__(self):
        return self.name

    def __repr__(self):
        return f'<Stage: {self.name}>'


class Permissions:
    def __init__(self, permissions):
        self.permissions = permissions

    def can_do(self, user, action):
        checks = self.permissions.get(action, list())
        return any(check(user) for check in checks)

    def can_edit(self, user):
        return self.can_do(user, 'edit')

    def can_review(self, user):
        return self.can_do(user, 'review')

    def can_view(self, user):
        return self.can_do(user, 'view')


staff_can = lambda user: user.is_apply_staff  # NOQA

applicant_can = lambda user: user.is_applicant  # NOQA

reviewer_can = lambda user: user.is_reviewer  # NOQA

partner_can = lambda user: user.is_partner  # NOQA

community_can = lambda user: user.is_community_reviewer  # NOQA


def make_permissions(edit=list(), review=list(), view=[staff_can, applicant_can, reviewer_can, partner_can, ]):
    return {
        'edit': edit,
        'review': review,
        'view': view,
    }


no_permissions = make_permissions()

default_permissions = make_permissions(edit=[staff_can], review=[staff_can])

hidden_from_applicant_permissions = make_permissions(edit=[staff_can], review=[staff_can], view=[staff_can, reviewer_can])

reviewer_review_permissions = make_permissions(edit=[staff_can, partner_can], review=[staff_can, reviewer_can, partner_can])

community_review_permissions = make_permissions(edit=[staff_can], review=[staff_can, reviewer_can, community_can])

applicant_edit_permissions = make_permissions(edit=[applicant_can, partner_can], review=[staff_can])

staff_applicant_edit_permissions = make_permissions(edit=[staff_can, applicant_can])

staff_edit_permissions = make_permissions(edit=[staff_can])


Request = Stage('Request', False)

RequestExt = Stage('RequestExt', True)

RequestCom = Stage('RequestCom', True)

Concept = Stage('Concept', False)

Proposal = Stage('Proposal', True)


INITIAL_STATE = 'in_discussion'

SingleStageDefinition = [
    {
        INITIAL_STATE: {
            'transitions': {
                'more_info': 'Request More Information',
                'internal_review': 'Open Review',
                'determination': 'Ready For Determination',
                'rejected': 'Dismiss',
                'accepted': 'Accept',
            },
            'display': 'Screening',
            'public': 'Application Received',
            'stage': Request,
            'permissions': default_permissions,
        },
        'more_info': {
            'transitions': {
                INITIAL_STATE: {
                    'display': 'Submit',
                    'permissions': {UserPermissions.APPLICANT, UserPermissions.STAFF, UserPermissions.LEAD, UserPermissions.ADMIN},
                    'method': 'create_revision',
                },
                'determination': 'Ready For Determination',
                'accepted': 'Accept',
                'rejected': 'Dismiss',
            },
            'display': 'More information required',
            'stage': Request,
            'permissions': applicant_edit_permissions,
        },
    },
    {
        'internal_review': {
            'transitions': {
                'post_review_discussion': 'Close Review',
                INITIAL_STATE: 'Screening (back)',
            },
            'display': 'Internal Review',
            'public': f'{settings.ORG_SHORT_NAME} Review',
            'stage': Request,
            'permissions': default_permissions,
        },
    },
    {
        'post_review_discussion': {
            'transitions': {
                'post_review_more_info': 'Request More Information',
                'determination': 'Ready For Determination',
                'internal_review': 'Open Review (back)',
                'accepted': 'Accept',
                'rejected': 'Dismiss',
            },
            'display': 'Ready For Discussion',
            'stage': Request,
            'permissions': hidden_from_applicant_permissions,
        },
        'post_review_more_info': {
            'transitions': {
                'post_review_discussion': {
                    'display': 'Submit',
                    'permissions': {UserPermissions.APPLICANT, UserPermissions.STAFF, UserPermissions.LEAD, UserPermissions.ADMIN},
                    'method': 'create_revision',
                },
                'determination': 'Ready For Determination',
                'accepted': 'Accept',
                'rejected': 'Dismiss',
            },
            'display': 'More information required',
            'stage': Request,
            'permissions': applicant_edit_permissions,
        },
    },
    {
        'determination': {
            'transitions': {
                'accepted': 'Accept',
                'rejected': 'Dismiss',
            },
            'display': 'Ready for Determination',
            'permissions': hidden_from_applicant_permissions,
            'stage': Request,
        },
    },
    {
        'accepted': {
            'display': 'Accepted',
            'future': 'Application Outcome',
            'stage': Request,
            'permissions': staff_applicant_edit_permissions,
        },
        'rejected': {
            'display': 'Dismissed',
            'stage': Request,
            'permissions': no_permissions,
        },
    },
]

SingleStageExternalDefinition = [
    {
        INITIAL_STATE: {
            'transitions': {
                'ext_more_info': 'Request More Information',
                'ext_internal_review': 'Open Review',
                'ext_determination': 'Ready For Determination',
                'ext_rejected': 'Dismiss',
            },
            'display': 'Screening',
            'public': 'Application Received',
            'stage': RequestExt,
            'permissions': default_permissions,
        },
        'ext_more_info': {
            'transitions': {
                INITIAL_STATE: {
                    'display': 'Submit',
                    'permissions': {UserPermissions.APPLICANT, UserPermissions.STAFF, UserPermissions.LEAD, UserPermissions.ADMIN},
                    'method': 'create_revision',
                },
            },
            'display': 'More information required',
            'stage': RequestExt,
            'permissions': applicant_edit_permissions,
        },
    },
    {
        'ext_internal_review': {
            'transitions': {
                'ext_post_review_discussion': 'Close Review',
                INITIAL_STATE: 'Screening (back)',
            },
            'display': 'Internal Review',
            'public': f'{settings.ORG_SHORT_NAME} Review',
            'stage': RequestExt,
            'permissions': default_permissions,
        },
    },
    {
        'ext_post_review_discussion': {
            'transitions': {
                'ext_post_review_more_info': 'Request More Information',
                'ext_external_review': 'Open AC review',
                'ext_determination': 'Ready For Determination',
                'ext_internal_review': 'Open Internal Review (back)',
                'ext_rejected': 'Dismiss',
            },
            'display': 'Ready For Discussion',
            'stage': RequestExt,
            'permissions': hidden_from_applicant_permissions,
        },
        'ext_post_review_more_info': {
            'transitions': {
                'ext_post_review_discussion': {
                    'display': 'Submit',
                    'permissions': {UserPermissions.APPLICANT, UserPermissions.STAFF, UserPermissions.LEAD, UserPermissions.ADMIN},
                    'method': 'create_revision',
                },
            },
            'display': 'More information required',
            'stage': RequestExt,
            'permissions': applicant_edit_permissions,
        },
    },
    {
        'ext_external_review': {
            'transitions': {
                'ext_post_external_review_discussion': 'Close Review',
                'ext_post_review_discussion': 'Ready For Discussion (back)',
            },
            'display': 'Advisory Council Review',
            'stage': RequestExt,
            'permissions': reviewer_review_permissions,
        },
    },
    {
        'ext_post_external_review_discussion': {
            'transitions': {
                'ext_post_external_review_more_info': 'Request More Information',
                'ext_determination': 'Ready For Determination',
                'ext_external_review': 'Open AC review (back)',
                'ext_accepted': 'Accept',
                'ext_rejected': 'Dismiss',
            },
            'display': 'Ready For Discussion',
            'stage': RequestExt,
            'permissions': hidden_from_applicant_permissions,
        },
        'ext_post_external_review_more_info': {
            'transitions': {
                'ext_post_external_review_discussion': {
                    'display': 'Submit',
                    'permissions': {UserPermissions.APPLICANT, UserPermissions.STAFF, UserPermissions.LEAD, UserPermissions.ADMIN},
                    'method': 'create_revision',
                },
            },
            'display': 'More information required',
            'stage': RequestExt,
            'permissions': applicant_edit_permissions,
        },
    },
    {
        'ext_determination': {
            'transitions': {
                'ext_accepted': 'Accept',
                'ext_rejected': 'Dismiss',
            },
            'display': 'Ready for Determination',
            'permissions': hidden_from_applicant_permissions,
            'stage': RequestExt,
        },
    },
    {
        'ext_accepted': {
            'display': 'Accepted',
            'future': 'Application Outcome',
            'stage': RequestExt,
            'permissions': staff_applicant_edit_permissions,
        },
        'ext_rejected': {
            'display': 'Dismissed',
            'stage': RequestExt,
            'permissions': no_permissions,
        },
    },
]


SingleStageCommunityDefinition = [
    {
        INITIAL_STATE: {
            'transitions': {
                'com_more_info': 'Request More Information',
                'com_open_call': 'Open Call (public)',
                'com_internal_review': 'Open Review',
                'com_community_review': 'Open Community Review',
                'com_determination': 'Ready For Determination',
                'com_rejected': 'Dismiss',
            },
            'display': 'Screening',
            'public': 'Application Received',
            'stage': RequestCom,
            'permissions': default_permissions,
        },
        'com_more_info': {
            'transitions': {
                INITIAL_STATE: {
                    'display': 'Submit',
                    'permissions': {UserPermissions.APPLICANT, UserPermissions.STAFF, UserPermissions.LEAD, UserPermissions.ADMIN},
                    'method': 'create_revision',
                },
            },
            'display': 'More information required',
            'stage': RequestCom,
            'permissions': applicant_edit_permissions,
        },
        'com_open_call': {
            'transitions': {
                INITIAL_STATE: 'Screening (back)',
                'com_rejected': 'Dismiss',
            },
            'display': 'Open Call (public)',
            'stage': RequestCom,
            'permissions': staff_edit_permissions,
        },
    },
    {
        'com_internal_review': {
            'transitions': {
                'com_community_review': 'Open Community Review',
                'com_post_review_discussion': 'Close Review',
                INITIAL_STATE: 'Screening (back)',
                'com_rejected': 'Dismiss',
            },
            'display': 'Internal Review',
            'public': f'{settings.ORG_SHORT_NAME} Review',
            'stage': RequestCom,
            'permissions': default_permissions,
        },
        'com_community_review': {
            'transitions': {
                'com_post_review_discussion': 'Close Review',
                'com_internal_review': 'Open Internal Review (back)',
                'com_rejected': 'Dismiss',
            },
            'display': 'Community Review',
            'public': f'{settings.ORG_SHORT_NAME} Review',
            'stage': RequestCom,
            'permissions': community_review_permissions,
        },
    },
    {
        'com_post_review_discussion': {
            'transitions': {
                'com_post_review_more_info': 'Request More Information',
                'com_external_review': 'Open AC review',
                'com_determination': 'Ready For Determination',
                'com_internal_review': 'Open Internal Review (back)',
                'com_rejected': 'Dismiss',
            },
            'display': 'Ready For Discussion',
            'stage': RequestCom,
            'permissions': hidden_from_applicant_permissions,
        },
        'com_post_review_more_info': {
            'transitions': {
                'com_post_review_discussion': {
                    'display': 'Submit',
                    'permissions': {UserPermissions.APPLICANT, UserPermissions.STAFF, UserPermissions.LEAD, UserPermissions.ADMIN},
                    'method': 'create_revision',
                },
            },
            'display': 'More information required',
            'stage': RequestCom,
            'permissions': applicant_edit_permissions,
        },
    },
    {
        'com_external_review': {
            'transitions': {
                'com_post_external_review_discussion': 'Close Review',
                'com_post_review_discussion': 'Ready For Discussion (back)',
            },
            'display': 'Advisory Council Review',
            'stage': RequestCom,
            'permissions': reviewer_review_permissions,
        },
    },
    {
        'com_post_external_review_discussion': {
            'transitions': {
                'com_post_external_review_more_info': 'Request More Information',
                'com_determination': 'Ready For Determination',
                'com_external_review': 'Open AC review (back)',
                'com_accepted': 'Accept',
                'com_rejected': 'Dismiss',
            },
            'display': 'Ready For Discussion',
            'stage': RequestCom,
            'permissions': hidden_from_applicant_permissions,
        },
        'com_post_external_review_more_info': {
            'transitions': {
                'com_post_external_review_discussion': {
                    'display': 'Submit',
                    'permissions': {UserPermissions.APPLICANT, UserPermissions.STAFF, UserPermissions.LEAD, UserPermissions.ADMIN},
                    'method': 'create_revision',
                },
            },
            'display': 'More information required',
            'stage': RequestCom,
            'permissions': applicant_edit_permissions,
        },
    },
    {
        'com_determination': {
            'transitions': {
                'com_accepted': 'Accept',
                'com_rejected': 'Dismiss',
            },
            'display': 'Ready for Determination',
            'permissions': hidden_from_applicant_permissions,
            'stage': RequestCom,
        },
    },
    {
        'com_accepted': {
            'display': 'Accepted',
            'future': 'Application Outcome',
            'stage': RequestCom,
            'permissions': staff_applicant_edit_permissions,
        },
        'com_rejected': {
            'display': 'Dismissed',
            'stage': RequestCom,
            'permissions': no_permissions,
        },
    },
]


DoubleStageDefinition = [
    {
        INITIAL_STATE: {
            'transitions': {
                'concept_more_info': 'Request More Information',
                'concept_internal_review': 'Open Review',
                'concept_determination': 'Ready For Preliminary Determination',
                'invited_to_proposal': 'Invite to Proposal',
                'concept_rejected': 'Dismiss',
            },
            'display': 'Screening',
            'public': 'Concept Note Received',
            'stage': Concept,
            'permissions': default_permissions,
        },
        'concept_more_info': {
            'transitions': {
                INITIAL_STATE: {
                    'display': 'Submit',
                    'permissions': {UserPermissions.APPLICANT, UserPermissions.STAFF, UserPermissions.LEAD, UserPermissions.ADMIN},
                    'method': 'create_revision',
                },
                'concept_rejected': 'Dismiss',
                'invited_to_proposal': 'Invite to Proposal',
                'concept_determination': 'Ready For Preliminary Determination',
            },
            'display': 'More information required',
            'stage': Concept,
            'permissions': applicant_edit_permissions,
        },
    },
    {
        'concept_internal_review': {
            'transitions': {
                'concept_review_discussion': 'Close Review',
                INITIAL_STATE: 'Screening (back)',
                'invited_to_proposal': 'Invite to Proposal',
            },
            'display': 'Internal Review',
            'public': f'{settings.ORG_SHORT_NAME} Review',
            'stage': Concept,
            'permissions': default_permissions,
        },
    },
    {
        'concept_review_discussion': {
            'transitions': {
                'concept_review_more_info': 'Request More Information',
                'concept_determination': 'Ready For Preliminary Determination',
                'concept_internal_review': 'Open Review (back)',
                'invited_to_proposal': 'Invite to Proposal',
                'concept_rejected': 'Dismiss',
            },
            'display': 'Ready For Discussion',
            'stage': Concept,
            'permissions': hidden_from_applicant_permissions,
        },
        'concept_review_more_info': {
            'transitions': {
                'concept_review_discussion': {
                    'display': 'Submit',
                    'permissions': {UserPermissions.APPLICANT, UserPermissions.STAFF, UserPermissions.LEAD, UserPermissions.ADMIN},
                    'method': 'create_revision',
                },
                'invited_to_proposal': 'Invite to Proposal',
            },
            'display': 'More information required',
            'stage': Concept,
            'permissions': applicant_edit_permissions,
        },
    },
    {
        'concept_determination': {
            'transitions': {
                'concept_review_more_info': 'Request More Information',
                'invited_to_proposal': 'Invite to Proposal',
                'concept_rejected': 'Dismiss',
            },
            'display': 'Ready for Preliminary Determination',
            'permissions': hidden_from_applicant_permissions,
            'stage': Concept,
        },
    },
    {
        'invited_to_proposal': {
            'display': 'Concept Accepted',
            'future': 'Preliminary Determination',
            'transitions': {
                'draft_proposal': {
                    'display': 'Progress',
                    'method': 'progress_application',
                    'permissions': {UserPermissions.STAFF, UserPermissions.LEAD, UserPermissions.ADMIN},
                    'conditions': 'not_progressed',
                },
            },
            'stage': Concept,
            'permissions': no_permissions,
        },
        'concept_rejected': {
            'display': 'Dismissed',
            'stage': Concept,
            'permissions': no_permissions,
        },
    },
    {
        'draft_proposal': {
            'transitions': {
                'proposal_discussion': {'display': 'Submit', 'permissions': {UserPermissions.APPLICANT}, 'method': 'create_revision'},
                'external_review': 'Open AC review',
                'proposal_determination': 'Ready For Final Determination',
                'proposal_rejected': 'Dismiss',
            },
            'display': 'Invited for Proposal',
            'stage': Proposal,
            'permissions': applicant_edit_permissions,
        },
    },
    {
        'proposal_discussion': {
            'transitions': {
                'proposal_more_info': 'Request More Information',
                'proposal_internal_review': 'Open Review',
                'external_review': 'Open AC review',
                'proposal_determination': 'Ready For Final Determination',
                'proposal_rejected': 'Dismiss',
            },
            'display': 'Proposal Received',
            'stage': Proposal,
            'permissions': default_permissions,
        },
        'proposal_more_info': {
            'transitions': {
                'proposal_discussion': {
                    'display': 'Submit',
                    'permissions': {UserPermissions.APPLICANT, UserPermissions.STAFF, UserPermissions.LEAD, UserPermissions.ADMIN},
                    'method': 'create_revision',
                },
                'external_review': 'Open AC review',
                'proposal_determination': 'Ready For Final Determination',
                'proposal_rejected': 'Dismiss',
            },
            'display': 'More information required',
            'stage': Proposal,
            'permissions': applicant_edit_permissions,
        },
    },
    {
        'proposal_internal_review': {
            'transitions': {
                'post_proposal_review_discussion': 'Close Review',
                'proposal_discussion': 'Proposal Received (back)',
            },
            'display': 'Internal Review',
            'public': f'{settings.ORG_SHORT_NAME} Review',
            'stage': Proposal,
            'permissions': default_permissions,
        },
    },
    {
        'post_proposal_review_discussion': {
            'transitions': {
                'post_proposal_review_more_info': 'Request More Information',
                'external_review': 'Open AC review',
                'proposal_determination': 'Ready For Final Determination',
                'proposal_internal_review': 'Open Internal Review (back)',
                'proposal_rejected': 'Dismiss',
            },
            'display': 'Ready For Discussion',
            'stage': Proposal,
            'permissions': hidden_from_applicant_permissions,
        },
        'post_proposal_review_more_info': {
            'transitions': {
                'post_proposal_review_discussion': {
                    'display': 'Submit',
                    'permissions': {UserPermissions.APPLICANT, UserPermissions.STAFF, UserPermissions.LEAD, UserPermissions.ADMIN},
                    'method': 'create_revision',
                },
                'external_review': 'Open AC review',
            },
            'display': 'More information required',
            'stage': Proposal,
            'permissions': applicant_edit_permissions,
        },
    },
    {
        'external_review': {
            'transitions': {
                'post_external_review_discussion': 'Close Review',
                'post_proposal_review_discussion': 'Ready For Discussion (back)',
            },
            'display': 'Advisory Council Review',
            'stage': Proposal,
            'permissions': reviewer_review_permissions,
        },
    },
    {
        'post_external_review_discussion': {
            'transitions': {
                'post_external_review_more_info': 'Request More Information',
                'proposal_determination': 'Ready For Final Determination',
                'external_review': 'Open AC review (back)',
                'proposal_accepted': 'Accept',
                'proposal_rejected': 'Dismiss',
            },
            'display': 'Ready For Discussion',
            'stage': Proposal,
            'permissions': hidden_from_applicant_permissions,
        },
        'post_external_review_more_info': {
            'transitions': {
                'post_external_review_discussion': {
                    'display': 'Submit',
                    'permissions': {UserPermissions.APPLICANT, UserPermissions.STAFF, UserPermissions.LEAD, UserPermissions.ADMIN},
                    'method': 'create_revision',
                },
            },
            'display': 'More information required',
            'stage': Proposal,
            'permissions': applicant_edit_permissions,
        },
    },
    {
        'proposal_determination': {
            'transitions': {
                'proposal_accepted': 'Accept',
                'proposal_rejected': 'Dismiss',
                'post_external_review_discussion': 'Ready For Discussion (back)',
            },
            'display': 'Ready for Final Determination',
            'permissions': hidden_from_applicant_permissions,
            'stage': Proposal,
        },
    },
    {
        'proposal_accepted': {
            'display': 'Accepted',
            'future': 'Final Determination',
            'stage': Proposal,
            'permissions': staff_applicant_edit_permissions,
        },
        'proposal_rejected': {
            'display': 'Dismissed',
            'stage': Proposal,
            'permissions': no_permissions,
        },
    },
]


def unpack_phases(phases):
    for step, step_data in enumerate(phases):
        for name, phase_data in step_data.items():
            yield step, name, phase_data


def phase_data(phases):
    return {
        phase_name: Phase(phase_name, step=step, **phase_data)
        for step, phase_name, phase_data in unpack_phases(phases)
    }


Request = Workflow('Request', 'single', **phase_data(SingleStageDefinition))

RequestExternal = Workflow('Request with external review', 'single_ext', **phase_data(SingleStageExternalDefinition))

RequestCommunity = Workflow('Request with community review', 'single_com', **phase_data(SingleStageCommunityDefinition))

ConceptProposal = Workflow('Concept & Proposal', 'double', **phase_data(DoubleStageDefinition))


WORKFLOWS = {
    Request.admin_name: Request,
    RequestExternal.admin_name: RequestExternal,
    RequestCommunity.admin_name: RequestCommunity,
    ConceptProposal.admin_name: ConceptProposal,
}


# This is not a dictionary as the keys will clash for the first phase of each workflow
# We cannot find the transitions for the first stage in this instance
PHASES = list(itertools.chain.from_iterable(workflow.items() for workflow in WORKFLOWS.values()))


def get_stage_change_actions():
    changes = set()
    for workflow in WORKFLOWS.values():
        stage = None
        for phase in workflow.values():
            if phase.stage != stage and stage:
                changes.add(phase.name)
            stage = phase.stage

    return changes


STAGE_CHANGE_ACTIONS = get_stage_change_actions()


STATUSES = defaultdict(set)

for key, value in PHASES:
    STATUSES[value.display_name].add(key)

active_statuses = [
    status for status, _ in PHASES
    if 'accepted' not in status and 'rejected' not in status and 'invited' not in status
]


def get_review_active_statuses(user=None):
    reviews = set()

    for phase_name, phase in PHASES:
        if phase_name in active_statuses:
            if user is None:
                reviews.add(phase_name)
            elif phase.permissions.can_review(user):
                reviews.add(phase_name)
    return reviews


def get_review_statuses(user=None):
    reviews = set()

    for phase_name, phase in PHASES:
        if 'review' in phase_name and 'discussion' not in phase_name:
            if user is None:
                reviews.add(phase_name)
            elif phase.permissions.can_review(user):
                reviews.add(phase_name)
    return reviews


review_statuses = get_review_statuses()

DETERMINATION_PHASES = list(phase_name for phase_name, _ in PHASES if '_discussion' in phase_name)
DETERMINATION_RESPONSE_PHASES = [
    'post_review_discussion',
    'concept_review_discussion',
    'post_external_review_discussion',
    'ext_post_external_review_discussion',
    'com_post_external_review_discussion',
]


def get_determination_transitions():
    transitions = {}
    for phase_name, phase in PHASES:
        for transition_name in phase.transitions:
            if 'accepted' in transition_name:
                transitions[transition_name] = 'accepted'
            elif 'rejected' in transition_name:
                transitions[transition_name] = 'rejected'
            elif 'more_info' in transition_name:
                transitions[transition_name] = 'more_info'
            elif 'invited_to_proposal' in transition_name:
                transitions[transition_name] = 'accepted'

    return transitions


def get_action_mapping(workflow):
    # Maps action names to the phase they originate from
    transitions = defaultdict(lambda: {'display': '', 'transitions': []})
    if workflow:
        phases = workflow.items()
    else:
        phases = PHASES
    for phase_name, phase in phases:
        for transition_name, transition in phase.transitions.items():
            transition_display = transition['display']
            transition_key = slugify(transition_display)
            transitions[transition_key]['transitions'].append(transition_name)
            transitions[transition_key]['display'] = transition_display

    return transitions


DETERMINATION_OUTCOMES = get_determination_transitions()


def phases_matching(phrase, exclude=list()):
    return [
        status for status, _ in PHASES
        if status.endswith(phrase) and status not in exclude
    ]


PHASES_MAPPING = {
    'received': {
        'name': 'Received',
        'statuses': [INITIAL_STATE, 'proposal_discussion'],
    },
    'internal-review': {
        'name': 'Internal Review',
        'statuses': phases_matching('internal_review'),
    },
    'in-discussion': {
        'name': 'Ready for Discussion',
        'statuses': phases_matching('discussion', exclude=[INITIAL_STATE, 'proposal_discussion']),
    },
    'more-information': {
        'name': 'More Information Requested',
        'statuses': phases_matching('more_info'),
    },
    'invited-for-proposal': {
        'name': 'Invited for Proposal',
        'statuses': ['draft_proposal'],
    },
    'external-review': {
        'name': 'AC Review',
        'statuses': phases_matching('external_review'),
    },
    'ready-for-determination': {
        'name': 'Ready for Determination',
        'statuses': phases_matching('determination'),
    },
    'accepted': {
        'name': 'Accepted',
        'statuses': phases_matching('accepted'),
    },
    'dismissed': {
        'name': 'Dismissed',
        'statuses': phases_matching('rejected'),
    },
}

OPEN_CALL_PHASES = [
    'com_open_call',
]

COMMUNITY_REVIEW_PHASES = [
    'com_community_review',
]
