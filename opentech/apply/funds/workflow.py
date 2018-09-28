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


class Phase:
    def __init__(self, name, display, stage, permissions, step, transitions=dict()):
        self.name = name
        self.display_name = display
        self.stage = stage
        self.permissions = permissions
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


class Stage:
    def __init__(self, name, has_external_review=False):
        self.name = name
        self.has_external_review = has_external_review

    def __str__(self):
        return self.name


class BasePermissions:
    def can_edit(self, user: 'User') -> bool:
        if user.is_apply_staff:
            return self.can_staff_edit(user)

        if user.is_applicant:
            return self.can_applicant_edit(user)

    def can_staff_edit(self, user: 'User') -> bool:
        return False

    def can_applicant_edit(self, user: 'User') -> bool:
        return False

    def can_review(self, user: 'User') -> bool:
        if user.is_apply_staff:
            return self.can_staff_review(user)

        if user.is_reviewer:
            return self.can_reviewer_review(user)

    def can_staff_review(self, user: 'User') -> bool:
        return False

    def can_reviewer_review(self, user: 'User') -> bool:
        return False


class NoPermissions(BasePermissions):
    pass


class DefaultPermissions(BasePermissions):
    # Other Permissions should inherit from this class
    # Staff can review at any time
    def can_staff_review(self, user: 'User') -> bool:
        return True

    def can_staff_edit(self, user: 'User') -> bool:
        return True


class ReviewerReviewPermissions(DefaultPermissions):
    def can_reviewer_review(self, user: 'User') -> bool:
        return True


class CanEditPermissions(DefaultPermissions):
    def can_applicant_edit(self, user: 'User') -> bool:
        return True

    def can_staff_edit(self, user: 'User') -> bool:
        # Prevent staff editing whilst with the user for edits
        return False


Request = Stage('Request', False)

Concept = Stage('Concept', False)

Proposal = Stage('Proposal', True)


INITIAL_STATE = 'in_discussion'

SingleStageDefinition = {
    INITIAL_STATE: {
        'transitions': {
            'internal_review': 'Open Review',
            'rejected': {'display': 'Reject', 'permissions': {UserPermissions.ADMIN, UserPermissions.LEAD}},
            'more_info': 'Request More Information',
        },
        'display': 'Under Discussion',
        'stage': Request,
        'permissions': DefaultPermissions(),
        'step': 0,
    },
    'more_info': {
        'transitions': {
            INITIAL_STATE: {
                'display': 'Submit',
                'permissions': {UserPermissions.APPLICANT, UserPermissions.LEAD, UserPermissions.ADMIN},
                'method': 'create_revision',
            },
        },
        'display': 'More information required',
        'stage': Request,
        'permissions': CanEditPermissions(),
        'step': 0,
    },
    'internal_review': {
        'transitions': {
            'post_review_discussion': 'Close Review',
        },
        'display': 'Internal Review',
        'stage': Request,
        'permissions': DefaultPermissions(),
        'step': 1,
    },
    'post_review_discussion': {
        'transitions': {
            'accepted': {'display': 'Accept', 'permissions': {UserPermissions.ADMIN, UserPermissions.LEAD}},
            'rejected': {'display': 'Reject', 'permissions': {UserPermissions.ADMIN, UserPermissions.LEAD}},
            'post_review_more_info': 'Request More Information',
        },
        'display': 'Under Discussion',
        'stage': Request,
        'permissions': DefaultPermissions(),
        'step': 2,
    },
    'post_review_more_info': {
        'transitions': {
            'post_review_discussion': {
                'display': 'Submit',
                'permissions': {UserPermissions.APPLICANT, UserPermissions.LEAD, UserPermissions.ADMIN},
                'method': 'create_revision',
            },
        },
        'display': 'More information required',
        'stage': Request,
        'permissions': CanEditPermissions(),
        'step': 2,
    },

    'accepted': {
        'display': 'Accepted',
        'stage': Request,
        'permissions': NoPermissions(),
        'step': 3,
    },
    'rejected': {
        'display': 'Rejected',
        'stage': Request,
        'permissions': NoPermissions(),
        'step': 3,
    },
}


DoubleStageDefinition = {
    INITIAL_STATE: {
        'transitions': {
            'concept_internal_review': 'Open Review',
            'concept_rejected': {'display': 'Reject', 'permissions': {UserPermissions.ADMIN, UserPermissions.LEAD}},
            'concept_more_info': 'Request More Information',
        },
        'display': 'Under Discussion',
        'stage': Concept,
        'permissions': DefaultPermissions(),
        'step': 0,
    },
    'concept_more_info': {
        'transitions': {
            INITIAL_STATE: {
                'display': 'Submit',
                'permissions': {UserPermissions.APPLICANT, UserPermissions.LEAD, UserPermissions.ADMIN},
                'method': 'create_revision',
            },
        },
        'display': 'More information required',
        'stage': Concept,
        'permissions': CanEditPermissions(),
        'step': 0,
    },
    'concept_internal_review': {
        'transitions': {
            'concept_review_discussion': 'Close Review',
        },
        'display': 'Internal Review',
        'stage': Concept,
        'permissions': DefaultPermissions(),
        'step': 1,
    },
    'concept_review_discussion': {
        'transitions': {
            'invited_to_proposal': {'display': 'Invite to Proposal', 'permissions': {UserPermissions.ADMIN, UserPermissions.LEAD}},
            'concept_rejected': {'display': 'Reject', 'permissions': {UserPermissions.ADMIN, UserPermissions.LEAD}},
            'concept_review_more_info': 'Request More Information',
        },
        'display': 'Under Discussion',
        'stage': Concept,
        'permissions': DefaultPermissions(),
        'step': 2,
    },
    'concept_review_more_info': {
        'transitions': {
            'concept_review_discussion': {
                'display': 'Submit',
                'permissions': {UserPermissions.APPLICANT, UserPermissions.LEAD, UserPermissions.ADMIN},
                'method': 'create_revision',
            },
        },
        'display': 'More information required',
        'stage': Concept,
        'permissions': CanEditPermissions(),
        'step': 2,
    },
    'invited_to_proposal': {
        'display': 'Concept Accepted',
        'transitions': {
            'draft_proposal': {
                'display': 'Progress',
                'method': 'progress_application',
                'permissions': {UserPermissions.ADMIN, UserPermissions.LEAD},
                'conditions': 'not_progressed',
            },
        },
        'stage': Concept,
        'permissions': NoPermissions(),
        'step': 3,
    },
    'concept_rejected': {
        'display': 'Rejected',
        'stage': Concept,
        'permissions': NoPermissions(),
        'step': 3,
    },
    'draft_proposal': {
        'transitions': {
            'proposal_discussion': {'display': 'Submit', 'permissions': {UserPermissions.APPLICANT}, 'method': 'create_revision'},
        },
        'display': 'Invited for Proposal',
        'stage': Proposal,
        'permissions': CanEditPermissions(),
        'step': 4,
    },
    'proposal_discussion': {
        'transitions': {
            'proposal_internal_review': 'Open Review',
            'proposal_rejected': {'display': 'Reject', 'permissions': {UserPermissions.ADMIN, UserPermissions.LEAD}},
            'proposal_more_info': 'Request More Information',
        },
        'display': 'Under Discussion',
        'stage': Proposal,
        'permissions': DefaultPermissions(),
        'step': 5,
    },
    'proposal_more_info': {
        'transitions': {
            'proposal_discussion': {
                'display': 'Submit',
                'permissions': {UserPermissions.APPLICANT, UserPermissions.LEAD, UserPermissions.ADMIN},
                'method': 'create_revision',
            },
        },
        'display': 'More information required',
        'stage': Proposal,
        'permissions': CanEditPermissions(),
        'step': 5,
    },
    'proposal_internal_review': {
        'transitions': {
            'post_proposal_review_discussion': 'Close Review',
        },
        'display': 'Internal Review',
        'stage': Proposal,
        'permissions': DefaultPermissions(),
        'step': 6,
    },
    'post_proposal_review_discussion': {
        'transitions': {
            'external_review': 'Open AC review',
            'proposal_rejected': {'display': 'Reject', 'permissions': {UserPermissions.ADMIN, UserPermissions.LEAD}},
            'post_proposal_review_more_info': 'Request More Information',
        },
        'display': 'Under Discussion',
        'stage': Proposal,
        'permissions': DefaultPermissions(),
        'step': 7,
    },
    'post_proposal_review_more_info': {
        'transitions': {
            'post_proposal_review_discussion': {
                'display': 'Submit',
                'permissions': {UserPermissions.APPLICANT, UserPermissions.LEAD, UserPermissions.ADMIN},
                'method': 'create_revision',
            },
        },
        'display': 'More information required',
        'stage': Proposal,
        'permissions': CanEditPermissions(),
        'step': 7,
    },
    'external_review': {
        'transitions': {
            'post_external_review_discussion': 'Close Review',
        },
        'display': 'Advisory Council Review',
        'stage': Proposal,
        'permissions': ReviewerReviewPermissions(),
        'step': 8,
    },
    'post_external_review_discussion': {
        'transitions': {
            'proposal_accepted': {'display': 'Accept', 'permissions': {UserPermissions.ADMIN, UserPermissions.LEAD}},
            'proposal_rejected': {'display': 'Reject', 'permissions': {UserPermissions.ADMIN, UserPermissions.LEAD}},
            'post_external_review_more_info': 'Request More Information',
        },
        'display': 'Under Discussion',
        'stage': Proposal,
        'permissions': DefaultPermissions(),
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
        'permissions': CanEditPermissions(),
        'step': 9,
    },
    'proposal_accepted': {
        'display': 'Accepted',
        'stage': Proposal,
        'permissions': NoPermissions(),
        'step': 10,
    },
    'proposal_rejected': {
        'display': 'Rejected',
        'stage': Proposal,
        'permissions': NoPermissions(),
        'step': 10,
    },

}


Request = Workflow('Request', 'single', **{
    phase_name: Phase(phase_name, **phase_data)
    for phase_name, phase_data in SingleStageDefinition.items()
})


ConceptProposal = Workflow('Concept & Proposal', 'double', **{
    phase_name: Phase(phase_name, **phase_data)
    for phase_name, phase_data in DoubleStageDefinition.items()
})


WORKFLOWS = {
    Request.admin_name: Request,
    ConceptProposal.admin_name: ConceptProposal,
}


PHASES = dict(itertools.chain.from_iterable(workflow.items() for workflow in WORKFLOWS.values()))


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

for key, value in PHASES.items():
    STATUSES[value.display_name].add(key)


active_statuses = [
    status for status in PHASES
    if 'accepted' not in status and 'rejected' not in status and 'invited' not in status
]


def get_review_statuses(user=None):
    reviews = set()

    for phase_name, phase in PHASES.items():
        if 'review' in phase_name and 'discussion' not in phase_name:
            if user is None:
                reviews.add(phase_name)
            elif phase.permissions.can_review(user):
                reviews.add(phase_name)
    return reviews


review_statuses = get_review_statuses()

DETERMINATION_PHASES = list(phase_name for phase_name in PHASES if '_discussion' in phase_name)
DETERMINATION_RESPONSE_PHASES = [
    'post_review_discussion',
    'concept_review_discussion',
    'post_external_review_discussion',
]


def get_determination_transitions():
    transitions = {}
    for phase_name, phase in PHASES.items():
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
