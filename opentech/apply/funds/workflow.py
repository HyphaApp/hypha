from collections import defaultdict, namedtuple
import copy
import itertools

from typing import Dict, Iterable, Iterator, List, Sequence, Set, Type, Union, TYPE_CHECKING


if TYPE_CHECKING:
    from opentech.apply.users.models import User  # NOQA


class Phase:
    def __init__(self, name, display, stage, permissions, step, transitions=dict()):
        self.name = name
        self.display_name = display
        self.stage = stage
        self.permissions = permissions
        self.step = step
        self.transitions = transitions

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


INITAL_STATE = 'in_discussion'

SingleStage = {
    INITAL_STATE : {
        'transitions': {
            'internal_review' : 'Open Review',
            'rejected' : 'Reject',
        },
        'display': 'Under Discussion',
        'stage': Request,
        'permissions': Permission(),
        'step': 0,
    },
    'internal_review' : {
        'transitions': {
            'post_review_discussion' : 'Close Review',
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
        },
        'display': 'Under Discussion',
        'stage': Request,
        'permissions': Permission(),
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

DoubleStage = {
    INITAL_STATE : {
        'transitions': {
            'concept_internal_review' : 'Open Review',
            'concept_rejected' : 'Reject',
        },
        'display': 'Under Discussion',
        'stage': Concept,
        'permissions': Permission(),
        'step': 0,
    },
    'concept_internal_review' : {
        'transitions': {
            'concept_review_discussion' : 'Close Review',
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
        },
        'display': 'Under Discussion',
        'stage': Concept,
        'permissions': Permission(),
        'step': 2,
    },
    'concept_rejected': {
        'display': 'Rejected',
        'stage': Concept,
        'permissions': Permission(),
        'step': 3,
    },
    'invited_to_proposal': {
        'transitions': {
            'proposal_discussion' : 'Submit',
        },
        'display': 'Invited for Proposal',
        'stage': Proposal,
        'permissions': Permission(),
        'step': 3,
    },
    'proposal_discussion' : {
        'transitions': {
            'proposal_internal_review' : 'Open Review',
            'proposal_rejected': 'Reject',
        },
        'display': 'Under Discussion',
        'stage': Proposal,
        'permissions': Permission(),
        'step': 4,
    },
    'proposal_internal_review' : {
        'transitions': {
            'post_proposal_review_discussion' : 'Close Review',
        },
        'display': 'Internal Review',
        'stage': Proposal,
        'permissions': StaffReviewPermission(),
        'step': 5,
    },
    'post_proposal_review_discussion': {
        'transitions': {
            'external_review': 'Open AC review',
            'proposal_rejected': 'Reject',
        },
        'display': 'Under Discussion',
        'stage': Proposal,
        'permissions': ReviewerReviewPermission(),
        'step': 6,
    },
    'external_review': {
        'transitions': {
            'post_external_review_discussion': 'Close Review',
        },
        'display': 'Advisory Council Review',
        'stage': Proposal,
        'permissions': Permission(),
        'step': 7,
    },
    'post_external_review_discussion': {
        'transitions': {
            'proposal_accepted': 'Accept',
            'proposal_rejected': 'Reject',
        },
        'display': 'Under Discussion',
        'stage': Proposal,
        'permissions': Permission(),
        'step': 8,
    },
    'proposal_accepted': {
        'display': 'Accepted',
        'stage': Proposal,
        'permissions': Permission(),
        'step': 9,
    },
    'proposal_rejected': {
        'display': 'Rejected',
        'stage': Proposal,
        'permissions': Permission(),
        'step': 9,
    },

}

PHASES = list(itertools.chain(SingleStage.items(), DoubleStage.items()))

STATUSES = defaultdict(set)

for key, value in PHASES:
    STATUSES[value['display']].add(key)

active_statuses = [
    status for status in PHASES
    if 'accepted' not in status or 'rejected' not in status
]


def get_review_statuses(user: Union[None, 'User']=None) -> Set[str]:
    reviews = set()

    for phase_name, phase in PHASES:
        if 'review' in phase_name:
            if user is None:
                reviews.add(phase_name)
            elif phase['permissions'].has_perm(user, 'review'):
                reviews.add(phase_name)
    return reviews

review_statuses = get_review_statuses()
