import itertools
from collections import defaultdict

from django.utils.text import slugify
from django.utils.translation import gettext as _

from .constants import DRAFT_STATE, INITIAL_STATE  # noqa
from .workflow import WORKFLOWS

"""
This file defines classes which allow you to compose workflows based on the following structure:

Workflow -> Stage -> Phase -> Action

Current limitations:
* Changing the name of a phase will mean that any object which references it cannot progress. [will
be fixed when streamfield, may require intermediate fix prior to launch]
* Do not reorder without looking at workflow automation steps in form_valid() in
hypha/apply/funds/views.py and hypha/apply/review/views.py.
"""


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


def get_ext_review_statuses():
    reviews = set()

    for phase_name, _phase in PHASES:
        if phase_name.endswith('external_review'):
            reviews.add(phase_name)
    return reviews


def get_ext_or_higher_statuses():
    """
    Returns a set of all the statuses for all workflow which are
    External Review or higher than that.
    """
    reviews = set()

    for workflow in WORKFLOWS.values():
        step = None
        for phase in workflow.values():
            if phase.name.endswith('external_review'):
                # Update the step for this workflow as External review state
                step = phase.step

            # Phase should have step higher or equal than External
            # review state for this workflow
            if step and phase.step >= step:
                reviews.add(phase.name)
    return reviews


def get_accepted_statuses():
    accepted_statuses = set()
    for phase_name, phase in PHASES:
        if phase.display_name == 'Accepted':
            accepted_statuses.add(phase_name)
    return accepted_statuses


def get_dismissed_statuses():
    dismissed_statuses = set()
    for phase_name, phase in PHASES:
        if phase.display_name == 'Dismissed':
            dismissed_statuses.add(phase_name)
    return dismissed_statuses


review_statuses = get_review_statuses()
ext_review_statuses = get_ext_review_statuses()
ext_or_higher_statuses = get_ext_or_higher_statuses()
accepted_statuses = get_accepted_statuses()
dismissed_statuses = get_dismissed_statuses()

DETERMINATION_PHASES = [phase_name for phase_name, _ in PHASES if '_discussion' in phase_name]
DETERMINATION_RESPONSE_PHASES = [
    'post_review_discussion',
    'concept_review_discussion',
    'post_external_review_discussion',
    'ext_post_external_review_discussion',
    'com_post_external_review_discussion',
]


def get_determination_transitions():
    transitions = {}
    for _phase_name, phase in PHASES:
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
    for _phase_name, phase in phases:
        for transition_name, transition in phase.transitions.items():
            transition_display = transition['display']
            transition_key = slugify(transition_display)
            transitions[transition_key]['transitions'].append(transition_name)
            transitions[transition_key]['display'] = transition_display

    return transitions


DETERMINATION_OUTCOMES = get_determination_transitions()


def phases_matching(phrase, exclude=None):
    if exclude is None:
        exclude = []
    return [
        status for status, _ in PHASES
        if status.endswith(phrase) and status not in exclude
    ]


PHASES_MAPPING = {
    'received': {
        'name': _('Received'),
        'statuses': [INITIAL_STATE, 'proposal_discussion'],
    },
    'internal-review': {
        'name': _('Internal Review'),
        'statuses': phases_matching('internal_review'),
    },
    'in-discussion': {
        'name': _('Ready for Discussion'),
        'statuses': phases_matching('discussion', exclude=[INITIAL_STATE, 'proposal_discussion']),
    },
    'more-information': {
        'name': _('More Information Requested'),
        'statuses': phases_matching('more_info'),
    },
    'invited-for-proposal': {
        'name': _('Invited for Proposal'),
        'statuses': ['draft_proposal'],
    },
    'external-review': {
        'name': _('External Review'),
        'statuses': phases_matching('external_review'),
    },
    'ready-for-determination': {
        'name': _('Ready for Determination'),
        'statuses': phases_matching('determination'),
    },
    'accepted': {
        'name': _('Accepted'),
        'statuses': phases_matching('accepted'),
    },
    'dismissed': {
        'name': _('Dismissed'),
        'statuses': phases_matching('rejected'),
    },
}

OPEN_CALL_PHASES = [
    'com_open_call',
]

COMMUNITY_REVIEW_PHASES = [
    'com_community_review',
]
