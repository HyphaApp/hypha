from opentech.apply.funds.workflow import DETERMINATION_OUTCOMES

from .models import TRANSITION_DETERMINATION


def determination_actions(user, submission):
    return [action[0] for action in submission.get_actions_for_user(user)]


def transition_from_outcome(outcome, submission):
    for transition_name in submission.phase.transitions:
        try:
            transition_type = TRANSITION_DETERMINATION[transition_name]
        except KeyError:
            pass
        else:
            if transition_type == outcome:
                return transition_name


def can_edit_determination(user, determination, submission):
    outcome = transition_from_outcome(determination.outcome, submission)
    valid_outcomes = determination_actions(user, submission)
    return outcome in valid_outcomes


def can_create_determination(user, submission):
    actions = determination_actions(user, submission)
    return any(action in DETERMINATION_OUTCOMES for action in actions)


def has_final_determination(submission):
    return submission.determinations.final().exists()
