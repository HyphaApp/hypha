"""
This file defines classes which allow you to compose workflows based on the following structure:

Workflow -> Stage -> Phase -> Action

Current limitations:
* Changing the name of a phase will mean that any object which references it cannot progress. [will
be fixed when streamfield, may require intermediate fix prior to launch]
* Do not reorder without looking at workflow automations steps in form_valid() in
hypha/apply/funds/views.py and hypha/apply/review/views.py.
"""

import itertools
from collections import defaultdict

from .definitions.double_stage import DoubleStageDefinition
from .definitions.single_stage import SingleStageDefinition
from .definitions.single_stage_community import SingleStageCommunityDefinition
from .definitions.single_stage_external import SingleStageExternalDefinition
from .definitions.single_stage_same import SingleStageSameDefinition
from .models.phase import Phase
from .models.workflow import Workflow


def phase_data(phases):
    """
    Transforms a workflow definition into a dictionary of Phase objects.

    Args:
        phases: A list of dictionaries defining the workflow phases and their configurations.

    Returns:
        dict: A dictionary where keys are phase names and values are Phase objects, each initialized
        with:
            - phase name
            - step number (order in workflow)
            - additional configuration data from the phase definition

    Example:
        Input phases = [
            {'draft': {'permissions': {...}}},
            {'review': {'permissions': {...}}}
        ]

        Returns = {
            'draft': Phase('draft', step=0, permissions={...}),
            'review': Phase('review', step=1, permissions={...})
        }
    """

    def unpack_phases(phases):
        return (
            (step, name, phase_data)
            for step, step_data in enumerate(phases)
            for name, phase_data in step_data.items()
        )

    return {
        phase_name: Phase(phase_name, step=step, **phase_data)
        for step, phase_name, phase_data in unpack_phases(phases)
    }


Request = Workflow("Request", "single", **phase_data(SingleStageDefinition))

RequestSameTime = Workflow(
    "Request with same time review",
    "single_same",
    **phase_data(SingleStageSameDefinition),
)

RequestExternal = Workflow(
    "Request with external review",
    "single_ext",
    **phase_data(SingleStageExternalDefinition),
)

RequestCommunity = Workflow(
    "Request with community review",
    "single_com",
    **phase_data(SingleStageCommunityDefinition),
)

ConceptProposal = Workflow(
    "Concept & Proposal", "double", **phase_data(DoubleStageDefinition)
)

WORKFLOWS = {
    Request.admin_name: Request,
    RequestSameTime.admin_name: RequestSameTime,
    RequestExternal.admin_name: RequestExternal,
    RequestCommunity.admin_name: RequestCommunity,
    ConceptProposal.admin_name: ConceptProposal,
}

PHASES = list(
    itertools.chain.from_iterable(workflow.items() for workflow in WORKFLOWS.values())
)

DETERMINATION_PHASES = [
    phase_name for phase_name, _ in PHASES if "_discussion" in phase_name
]

STATUSES = defaultdict(set)

for key, value in PHASES:
    STATUSES[value.display_name].add(key)

active_statuses = [
    status
    for status, _ in PHASES
    if "accepted" not in status and "rejected" not in status and "invited" not in status
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
        if "review" in phase_name and "discussion" not in phase_name:
            if user is None:
                reviews.add(phase_name)
            elif phase.permissions.can_review(user):
                reviews.add(phase_name)
    return reviews


def get_ext_review_statuses():
    reviews = set()

    for phase_name, _phase in PHASES:
        if phase_name.endswith("external_review"):
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
            if phase.name.endswith("external_review"):
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
        if phase.display_name == "Accepted":
            accepted_statuses.add(phase_name)
    return accepted_statuses


def get_dismissed_statuses():
    dismissed_statuses = set()
    for phase_name, phase in PHASES:
        if phase.display_name == "Dismissed":
            dismissed_statuses.add(phase_name)
    return dismissed_statuses


review_statuses = get_review_statuses()
ext_review_statuses = get_ext_review_statuses()
ext_or_higher_statuses = get_ext_or_higher_statuses()
accepted_statuses = get_accepted_statuses()
dismissed_statuses = get_dismissed_statuses()
