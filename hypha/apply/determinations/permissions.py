from hypha.apply.funds.workflows import DETERMINATION_OUTCOMES

from .utils import determination_actions, transition_from_outcome


def can_edit_determination(user, determination, submission):
    if submission.is_archive:
        return False
    outcome = transition_from_outcome(determination.outcome, submission)
    valid_outcomes = determination_actions(user, submission)
    return outcome in valid_outcomes


def can_create_determination(user, submission):
    if submission.is_archive:
        return False
    actions = determination_actions(user, submission)
    return any(action in DETERMINATION_OUTCOMES for action in actions)
