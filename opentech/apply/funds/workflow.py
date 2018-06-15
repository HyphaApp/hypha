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


class Permission:
    def can_edit(self, user: 'User') -> bool:
        return False

    def can_staff_review(self, user: 'User') -> bool:
        return False

    def can_reviewer_review(self, user: 'User') -> bool:
        return False

    def can_review(self, user: 'User') -> bool:
        return self.can_staff_review(user) or self.can_reviewer_review(user)


class StaffReviewPermission(Permission):
    def can_staff_review(self, user: 'User') -> bool:
        return user.is_apply_staff


class ReviewerReviewPermission(Permission):
    def can_reviewer_review(self, user: 'User') -> bool:
        return user.is_reviewer


class CanEditPermission(Permission):
    def can_edit(self, user: 'User') -> bool:
        return True


Request = Stage('Request', False)

Concept = Stage('Concept', False)

Proposal = Stage('Proposal', False)


INITIAL_STATE = 'in_discussion'

SingleStageDefinition = {
    INITIAL_STATE: {
        'transitions': {
            'internal_review': 'Open Review',
            'rejected': 'Reject',
            'more_info': 'Request More Information',
        },
        'display': 'Under Discussion',
        'stage': Request,
        'permissions': Permission(),
        'step': 0,
    },
    'more_info': {
        'transitions': {
            INITIAL_STATE: {'display': 'Submit', 'permissions': {UserPermissions.APPLICANT}},
        },
        'display': 'More information required',
        'stage': Request,
        'permissions': CanEditPermission(),
        'step': 0,
    },
    'internal_review': {
        'transitions': {
            'post_review_discussion': 'Close Review',
        },
        'display': 'Internal Review',
        'stage': Request,
        'permissions': StaffReviewPermission(),
        'step': 1,
    },
    'post_review_discussion': {
        'transitions': {
            'accepted': 'Accept',
            'rejected': 'Reject',
            'post_review_more_info': 'Request More Information',
        },
        'display': 'Under Discussion',
        'stage': Request,
        'permissions': Permission(),
        'step': 2,
    },
    'post_review_more_info': {
        'transitions': {
            'post_review_discussion': {'display': 'Submit', 'permissions': {UserPermissions.APPLICANT}},
        },
        'display': 'More information required',
        'stage': Request,
        'permissions': CanEditPermission(),
        'step': 2,
    },

    'accepted': {
        'display': 'Accepted',
        'stage': Request,
        'permissions': Permission(),
        'step': 3,
    },
    'rejected': {
        'display': 'Rejected',
        'stage': Request,
        'permissions': Permission(),
        'step': 3,
    },
}


DoubleStageDefinition = {
    INITIAL_STATE: {
        'transitions': {
            'concept_internal_review': 'Open Review',
            'concept_rejected': 'Reject',
            'concept_more_info': 'Request More Information',
        },
        'display': 'Under Discussion',
        'stage': Concept,
        'permissions': Permission(),
        'step': 0,
    },
    'concept_more_info': {
        'transitions': {
            INITIAL_STATE: {'display': 'Submit', 'permissions': {UserPermissions.APPLICANT}},
        },
        'display': 'More information required',
        'stage': Concept,
        'permissions': CanEditPermission(),
        'step': 0,
    },
    'concept_internal_review': {
        'transitions': {
            'concept_review_discussion': 'Close Review',
        },
        'display': 'Internal Review',
        'stage': Concept,
        'permissions': StaffReviewPermission(),
        'step': 1,
    },
    'concept_review_discussion': {
        'transitions': {
            'invited_to_proposal': 'Invite to Proposal',
            'concept_rejected': 'Reject',
            'concept_review_more_info': 'Request More Information',
        },
        'display': 'Under Discussion',
        'stage': Concept,
        'permissions': Permission(),
        'step': 2,
    },
    'concept_review_more_info': {
        'transitions': {
            'concept_review_discussion': {'display': 'Submit', 'permissions': {UserPermissions.APPLICANT}},
        },
        'display': 'More information required',
        'stage': Concept,
        'permissions': CanEditPermission(),
        'step': 2,
    },
    'invited_to_proposal': {
        'display': 'Concept Accepted',
        'transitions': {
            'draft_proposal': {'display': 'Progress', 'action': 'progress_application', 'form': False},
        },
        'stage': Concept,
        'permissions': Permission(),
        'step': 3,
    },
    'concept_rejected': {
        'display': 'Rejected',
        'stage': Concept,
        'permissions': Permission(),
        'step': 3,
    },
    'draft_proposal': {
        'transitions': {
            'proposal_discussion': {'display': 'Submit', 'permissions': {UserPermissions.APPLICANT}},
        },
        'display': 'Invited for Proposal',
        'stage': Proposal,
        'permissions': CanEditPermission(),
        'step': 4,
    },
    'proposal_discussion': {
        'transitions': {
            'proposal_internal_review': 'Open Review',
            'proposal_rejected': 'Reject',
            'proposal_more_info': 'Request More Information',
        },
        'display': 'Under Discussion',
        'stage': Proposal,
        'permissions': Permission(),
        'step': 5,
    },
    'proposal_more_info': {
        'transitions': {
            'proposal_discussion': {'display': 'Submit', 'permissions': {UserPermissions.APPLICANT}},
        },
        'display': 'More information required',
        'stage': Proposal,
        'permissions': CanEditPermission(),
        'step': 5,
    },
    'proposal_internal_review': {
        'transitions': {
            'post_proposal_review_discussion': 'Close Review',
        },
        'display': 'Internal Review',
        'stage': Proposal,
        'permissions': StaffReviewPermission(),
        'step': 6,
    },
    'post_proposal_review_discussion': {
        'transitions': {
            'external_review': 'Open AC review',
            'proposal_rejected': 'Reject',
            'post_proposal_review_more_info': 'Request More Information',
        },
        'display': 'Under Discussion',
        'stage': Proposal,
        'permissions': ReviewerReviewPermission(),
        'step': 7,
    },
    'post_proposal_review_more_info': {
        'transitions': {
            'post_proposal_review_discussion': {'display': 'Submit', 'permissions': {UserPermissions.APPLICANT}},
        },
        'display': 'More information required',
        'stage': Proposal,
        'permissions': CanEditPermission(),
        'step': 7,
    },
    'external_review': {
        'transitions': {
            'post_external_review_discussion': 'Close Review',
        },
        'display': 'Advisory Council Review',
        'stage': Proposal,
        'permissions': Permission(),
        'step': 8,
    },
    'post_external_review_discussion': {
        'transitions': {
            'proposal_accepted': 'Accept',
            'proposal_rejected': 'Reject',
            'post_external_review_more_info': 'Request More Information',
        },
        'display': 'Under Discussion',
        'stage': Proposal,
        'permissions': Permission(),
        'step': 9,
    },
    'post_external_review_more_info': {
        'transitions': {
            'post_external_review_discussion': {'display': 'Submit', 'permissions': {UserPermissions.APPLICANT}},
        },
        'display': 'More information required',
        'stage': Proposal,
        'permissions': CanEditPermission(),
        'step': 9,
    },
    'proposal_accepted': {
        'display': 'Accepted',
        'stage': Proposal,
        'permissions': Permission(),
        'step': 10,
    },
    'proposal_rejected': {
        'display': 'Rejected',
        'stage': Proposal,
        'permissions': Permission(),
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


PHASES = list(itertools.chain.from_iterable(workflow.items() for workflow in WORKFLOWS.values()))


STATUSES = defaultdict(set)

for key, value in PHASES:
    STATUSES[value.display_name].add(key)

active_statuses = [
    status for status, _ in PHASES
    if 'accepted' not in status or 'rejected' not in status or 'invited' not in status
]


def get_review_statuses(user=None):
    reviews = set()

    for phase_name, phase in PHASES:
        if 'review' in phase_name:
            if user is None:
                reviews.add(phase_name)
            elif phase.permissions.can_review(user):
                reviews.add(phase_name)
    return reviews


review_statuses = get_review_statuses()
