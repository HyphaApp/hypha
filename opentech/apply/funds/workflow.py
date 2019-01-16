from collections import defaultdict
from enum import Enum
import itertools


"""
This file defines classes which allow you to compose workflows based on the following structure:

Workflow -> Stage -> Phase -> Action

Current limitations:
* Changing the name of a phase will mean that any object which references it cannot progress. [will
be fixed when streamfield, may require intermediate fix prior to launch]
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
        self.public_name = public or self.display_name
        self.future_name = future or self.public_name
        self.stage = stage
        self.permissions = Permissions(permissions)
        self.step = step

        # For building transition methods on the parent
        self.transitions = {}

        default_permissions = {UserPermissions.STAFF, UserPermissions.ADMIN, UserPermissions.LEAD}

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
        return f'<Phase {self.display_name} ({self.public_name})>'


class Stage:
    def __init__(self, name, has_external_review=False):
        self.name = name
        self.has_external_review = has_external_review

    def __str__(self):
        return self.name


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


def make_permissions(edit=list(), review=list(), view=[staff_can, applicant_can, reviewer_can]):
    return {
        'edit': edit,
        'review': review,
        'view': view,
    }


no_permissions = make_permissions()

default_permissions = make_permissions(edit=[staff_can], review=[staff_can])

hidden_from_applicant_permissions = make_permissions(edit=[staff_can], review=[staff_can], view=[staff_can, reviewer_can])

reviewer_review_permissions = make_permissions(edit=[staff_can], review=[staff_can, reviewer_can])

applicant_edit_permissions = make_permissions(edit=[applicant_can], review=[staff_can])


Request = Stage('Request', False)

RequestExt = Stage('RequestExt', True)

Concept = Stage('Concept', False)

Proposal = Stage('Proposal', True)


INITIAL_STATE = 'in_discussion'

SingleStageDefinition = {
    INITIAL_STATE: {
        'transitions': {
            'internal_review': 'Open Review',
            'rejected': {'display': 'Dismiss', 'permissions': {UserPermissions.ADMIN, UserPermissions.LEAD}},
            'more_info': 'Request More Information',
            'accepted': {'display': 'Accept', 'permissions': {UserPermissions.ADMIN, UserPermissions.LEAD}},
        },
        'display': 'Screening',
        'public': 'Application Received',
        'stage': Request,
        'permissions': default_permissions,
        'step': 0,
    },
    'more_info': {
        'transitions': {
            INITIAL_STATE: {
                'display': 'Submit',
                'permissions': {UserPermissions.APPLICANT, UserPermissions.LEAD, UserPermissions.ADMIN},
                'method': 'create_revision',
            },
            'accepted': {'display': 'Accept', 'permissions': {UserPermissions.ADMIN, UserPermissions.LEAD}},
            'rejected': {'display': 'Dismiss', 'permissions': {UserPermissions.ADMIN, UserPermissions.LEAD}},
        },
        'display': 'More information required',
        'stage': Request,
        'permissions': applicant_edit_permissions,
        'step': 0,
    },
    'internal_review': {
        'transitions': {
            'post_review_discussion': 'Close Review',
        },
        'display': 'Internal Review',
        'public': 'OTF Review',
        'stage': Request,
        'permissions': default_permissions,
        'step': 1,
    },
    'post_review_discussion': {
        'transitions': {
            'accepted': {'display': 'Accept', 'permissions': {UserPermissions.ADMIN, UserPermissions.LEAD}},
            'rejected': {'display': 'Dismiss', 'permissions': {UserPermissions.ADMIN, UserPermissions.LEAD}},
            'post_review_more_info': 'Request More Information',
        },
        'display': 'Ready For Discussion',
        'stage': Request,
        'permissions': hidden_from_applicant_permissions,
        'step': 2,
    },
    'post_review_more_info': {
        'transitions': {
            'post_review_discussion': {
                'display': 'Submit',
                'permissions': {UserPermissions.APPLICANT, UserPermissions.LEAD, UserPermissions.ADMIN},
                'method': 'create_revision',
            },
            'accepted': {'display': 'Accept', 'permissions': {UserPermissions.ADMIN, UserPermissions.LEAD}},
            'rejected': {'display': 'Dismiss', 'permissions': {UserPermissions.ADMIN, UserPermissions.LEAD}},
        },
        'display': 'More information required',
        'stage': Request,
        'permissions': applicant_edit_permissions,
        'step': 2,
    },

    'accepted': {
        'display': 'Accepted',
        'future': 'Application Outcome',
        'stage': Request,
        'permissions': no_permissions,
        'step': 3,
    },
    'rejected': {
        'display': 'Dismissed',
        'stage': Request,
        'permissions': no_permissions,
        'step': 3,
    },
}

SingleStageExternalDefinition = {
    INITIAL_STATE: {
        'transitions': {
            'ext_internal_review': 'Open Review',
            'ext_rejected': {'display': 'Dismiss', 'permissions': {UserPermissions.ADMIN, UserPermissions.LEAD}},
            'ext_more_info': 'Request More Information',
        },
        'display': 'Screening',
        'public': 'Application Received',
        'stage': RequestExt,
        'permissions': default_permissions,
        'step': 0,
    },
    'ext_more_info': {
        'transitions': {
            INITIAL_STATE: {
                'display': 'Submit',
                'permissions': {UserPermissions.APPLICANT, UserPermissions.LEAD, UserPermissions.ADMIN},
                'method': 'create_revision',
            },
        },
        'display': 'More information required',
        'stage': RequestExt,
        'permissions': applicant_edit_permissions,
        'step': 0,
    },
    'ext_internal_review': {
        'transitions': {
            'ext_post_review_discussion': 'Close Review',
        },
        'display': 'Internal Review',
        'public': 'OTF Review',
        'stage': RequestExt,
        'permissions': default_permissions,
        'step': 1,
    },
    'ext_post_review_discussion': {
        'transitions': {
            'ext_external_review': 'Open AC review',
            'ext_rejected': {'display': 'Dismiss', 'permissions': {UserPermissions.ADMIN, UserPermissions.LEAD}},
            'ext_post_review_more_info': 'Request More Information',
        },
        'display': 'Ready For Discussion',
        'stage': RequestExt,
        'permissions': hidden_from_applicant_permissions,
        'step': 2,
    },
    'ext_post_review_more_info': {
        'transitions': {
            'ext_post_review_discussion': {
                'display': 'Submit',
                'permissions': {UserPermissions.APPLICANT, UserPermissions.LEAD, UserPermissions.ADMIN},
                'method': 'create_revision',
            },
        },
        'display': 'More information required',
        'stage': RequestExt,
        'permissions': applicant_edit_permissions,
        'step': 2,
    },
    'ext_external_review': {
        'transitions': {
            'ext_post_external_review_discussion': 'Close Review',
        },
        'display': 'Advisory Council Review',
        'stage': RequestExt,
        'permissions': reviewer_review_permissions,
        'step': 3,
    },
    'ext_post_external_review_discussion': {
        'transitions': {
            'ext_accepted': {'display': 'Accept', 'permissions': {UserPermissions.ADMIN, UserPermissions.LEAD}},
            'ext_rejected': {'display': 'Dismiss', 'permissions': {UserPermissions.ADMIN, UserPermissions.LEAD}},
            'ext_post_external_review_more_info': 'Request More Information',
        },
        'display': 'Ready for Discussion',
        'stage': RequestExt,
        'permissions': hidden_from_applicant_permissions,
        'step': 4,
    },
    'ext_post_external_review_more_info': {
        'transitions': {
            'ext_post_external_review_discussion': {
                'display': 'Submit',
                'permissions': {UserPermissions.APPLICANT, UserPermissions.LEAD, UserPermissions.ADMIN},
                'method': 'create_revision',
            },
        },
        'display': 'More information required',
        'stage': RequestExt,
        'permissions': applicant_edit_permissions,
        'step': 4,
    },

    'ext_accepted': {
        'display': 'Accepted',
        'future': 'Application Outcome',
        'stage': RequestExt,
        'permissions': no_permissions,
        'step': 5,
    },
    'ext_rejected': {
        'display': 'Dismissed',
        'stage': RequestExt,
        'permissions': no_permissions,
        'step': 5,
    },
}


DoubleStageDefinition = {
    INITIAL_STATE: {
        'transitions': {
            'concept_internal_review': 'Open Review',
            'concept_rejected': {'display': 'Dismiss', 'permissions': {UserPermissions.ADMIN, UserPermissions.LEAD}},
            'concept_more_info': 'Request More Information',
            'invited_to_proposal': {'display': 'Invite to Proposal', 'permissions': {UserPermissions.ADMIN, UserPermissions.LEAD}},
        },
        'display': 'Screening',
        'public': 'Concept Note Received',
        'stage': Concept,
        'permissions': default_permissions,
        'step': 0,
    },
    'concept_more_info': {
        'transitions': {
            INITIAL_STATE: {
                'display': 'Submit',
                'permissions': {UserPermissions.APPLICANT, UserPermissions.LEAD, UserPermissions.ADMIN},
                'method': 'create_revision',
            },
            'concept_rejected': {'display': 'Dismiss', 'permissions': {UserPermissions.ADMIN, UserPermissions.LEAD}},
            'invited_to_proposal': {'display': 'Invite to Proposal', 'permissions': {UserPermissions.ADMIN, UserPermissions.LEAD}},
        },
        'display': 'More information required',
        'stage': Concept,
        'permissions': applicant_edit_permissions,
        'step': 0,
    },
    'concept_internal_review': {
        'transitions': {
            'concept_review_discussion': 'Close Review',
            'invited_to_proposal': {'display': 'Invite to Proposal', 'permissions': {UserPermissions.ADMIN, UserPermissions.LEAD}},
        },
        'display': 'Internal Review',
        'public': 'OTF Review',
        'stage': Concept,
        'permissions': default_permissions,
        'step': 1,
    },
    'concept_review_discussion': {
        'transitions': {
            'invited_to_proposal': {'display': 'Invite to Proposal', 'permissions': {UserPermissions.ADMIN, UserPermissions.LEAD}},
            'concept_rejected': {'display': 'Dismiss', 'permissions': {UserPermissions.ADMIN, UserPermissions.LEAD}},
            'concept_review_more_info': 'Request More Information',
        },
        'display': 'Ready for Discussion',
        'stage': Concept,
        'permissions': hidden_from_applicant_permissions,
        'step': 2,
    },
    'concept_review_more_info': {
        'transitions': {
            'concept_review_discussion': {
                'display': 'Submit',
                'permissions': {UserPermissions.APPLICANT, UserPermissions.LEAD, UserPermissions.ADMIN},
                'method': 'create_revision',
            },
            'invited_to_proposal': {'display': 'Invite to Proposal', 'permissions': {UserPermissions.ADMIN, UserPermissions.LEAD}},
        },
        'display': 'More information required',
        'stage': Concept,
        'permissions': applicant_edit_permissions,
        'step': 2,
    },
    'invited_to_proposal': {
        'display': 'Concept Accepted',
        'future': 'Preliminary Decision',
        'transitions': {
            'draft_proposal': {
                'display': 'Progress',
                'method': 'progress_application',
                'permissions': {UserPermissions.ADMIN, UserPermissions.LEAD},
                'conditions': 'not_progressed',
            },
        },
        'stage': Concept,
        'permissions': no_permissions,
        'step': 3,
    },
    'concept_rejected': {
        'display': 'Dismissed',
        'stage': Concept,
        'permissions': no_permissions,
        'step': 3,
    },
    'draft_proposal': {
        'transitions': {
            'proposal_discussion': {'display': 'Submit', 'permissions': {UserPermissions.APPLICANT}, 'method': 'create_revision'},
            'proposal_rejected': {'display': 'Dismiss', 'permissions': {UserPermissions.ADMIN, UserPermissions.LEAD}},
            'external_review': 'Open AC review',
        },
        'display': 'Invited for Proposal',
        'stage': Proposal,
        'permissions': applicant_edit_permissions,
        'step': 4,
    },
    'proposal_discussion': {
        'transitions': {
            'proposal_internal_review': 'Open Review',
            'proposal_rejected': {'display': 'Dismiss', 'permissions': {UserPermissions.ADMIN, UserPermissions.LEAD}},
            'proposal_more_info': 'Request More Information',
            'external_review': 'Open AC review',
        },
        'display': 'Ready For Discussion',
        'public': 'Proposal Received',
        'stage': Proposal,
        'permissions': default_permissions,
        'step': 5,
    },
    'proposal_more_info': {
        'transitions': {
            'proposal_discussion': {
                'display': 'Submit',
                'permissions': {UserPermissions.APPLICANT, UserPermissions.LEAD, UserPermissions.ADMIN},
                'method': 'create_revision',
            },
            'proposal_rejected': {'display': 'Dismiss', 'permissions': {UserPermissions.ADMIN, UserPermissions.LEAD}},
            'external_review': 'Open AC review',
        },
        'display': 'More information required',
        'stage': Proposal,
        'permissions': applicant_edit_permissions,
        'step': 5,
    },
    'proposal_internal_review': {
        'transitions': {
            'post_proposal_review_discussion': 'Close Review',
        },
        'display': 'Internal Review',
        'public': 'OTF Review',
        'stage': Proposal,
        'permissions': default_permissions,
        'step': 6,
    },
    'post_proposal_review_discussion': {
        'transitions': {
            'external_review': 'Open AC review',
            'proposal_rejected': {'display': 'Dismiss', 'permissions': {UserPermissions.ADMIN, UserPermissions.LEAD}},
            'post_proposal_review_more_info': 'Request More Information',
        },
        'display': 'Ready for Discussion',
        'stage': Proposal,
        'permissions': hidden_from_applicant_permissions,
        'step': 7,
    },
    'post_proposal_review_more_info': {
        'transitions': {
            'post_proposal_review_discussion': {
                'display': 'Submit',
                'permissions': {UserPermissions.APPLICANT, UserPermissions.LEAD, UserPermissions.ADMIN},
                'method': 'create_revision',
            },
            'external_review': 'Open AC review',
        },
        'display': 'More information required',
        'stage': Proposal,
        'permissions': applicant_edit_permissions,
        'step': 7,
    },
    'external_review': {
        'transitions': {
            'post_external_review_discussion': 'Close Review',
        },
        'display': 'Advisory Council Review',
        'stage': Proposal,
        'permissions': reviewer_review_permissions,
        'step': 8,
    },
    'post_external_review_discussion': {
        'transitions': {
            'proposal_accepted': {'display': 'Accept', 'permissions': {UserPermissions.ADMIN, UserPermissions.LEAD}},
            'proposal_rejected': {'display': 'Dismiss', 'permissions': {UserPermissions.ADMIN, UserPermissions.LEAD}},
            'post_external_review_more_info': 'Request More Information',
        },
        'display': 'Ready for Discussion',
        'stage': Proposal,
        'permissions': hidden_from_applicant_permissions,
        'step': 9,
    },
    'post_external_review_more_info': {
        'transitions': {
            'post_external_review_discussion': {
                'display': 'Submit',
                'permissions': {UserPermissions.APPLICANT, UserPermissions.LEAD, UserPermissions.ADMIN},
                'method': 'create_revision',
            },
        },
        'display': 'More information required',
        'stage': Proposal,
        'permissions': applicant_edit_permissions,
        'step': 9,
    },
    'proposal_accepted': {
        'display': 'Accepted',
        'future': 'Application Outcome',
        'stage': Proposal,
        'permissions': no_permissions,
        'step': 10,
    },
    'proposal_rejected': {
        'display': 'Dismissed',
        'stage': Proposal,
        'permissions': no_permissions,
        'step': 10,
    },

}


Request = Workflow('Request', 'single', **{
    phase_name: Phase(phase_name, **phase_data)
    for phase_name, phase_data in SingleStageDefinition.items()
})

RequestExternal = Workflow('Request with external review', 'single_ext', **{
    phase_name: Phase(phase_name, **phase_data)
    for phase_name, phase_data in SingleStageExternalDefinition.items()
})

ConceptProposal = Workflow('Concept & Proposal', 'double', **{
    phase_name: Phase(phase_name, **phase_data)
    for phase_name, phase_data in DoubleStageDefinition.items()
})


WORKFLOWS = {
    Request.admin_name: Request,
    RequestExternal.admin_name: RequestExternal,
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


DETERMINATION_OUTCOMES = get_determination_transitions()
