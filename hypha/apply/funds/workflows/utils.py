from collections import defaultdict

from django.utils.text import slugify


def phases_matching(phrase, exclude=None):
    from .registry import PHASES

    if exclude is None:
        exclude = []
    return [
        status
        for status, _ in PHASES
        if status.endswith(phrase) and status not in exclude
    ]


def get_stage_change_actions():
    from .registry import WORKFLOWS

    changes = set()
    for workflow in WORKFLOWS.values():
        stage = None
        for phase in workflow.values():
            if phase.stage != stage and stage:
                changes.add(phase.name)
            stage = phase.stage
    return changes


def get_determination_transitions():
    from .registry import PHASES

    transitions = {}
    for _phase_name, phase in PHASES:
        for transition_name in phase.transitions:
            if "accepted" in transition_name:
                transitions[transition_name] = "accepted"
            elif "rejected" in transition_name:
                transitions[transition_name] = "rejected"
            elif "more_info" in transition_name:
                transitions[transition_name] = "more_info"
            elif "invited_to_proposal" in transition_name:
                transitions[transition_name] = "accepted"

    return transitions


def get_action_mapping(workflow):
    from .registry import PHASES

    # Maps action names to the phase they originate from
    transitions = defaultdict(lambda: {"display": "", "transitions": []})
    if workflow:
        phases = workflow.items()
    else:
        phases = PHASES
    for _phase_name, phase in phases:
        for transition_name, transition in phase.transitions.items():
            transition_display = transition["display"]
            transition_key = slugify(transition_display)
            transitions[transition_key]["transitions"].append(transition_name)
            transitions[transition_key]["display"] = transition_display

    return transitions
