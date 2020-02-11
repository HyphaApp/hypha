from opentech.apply.funds.workflow import DETERMINATION_OUTCOMES

from .models import DETERMINATION_TO_OUTCOME, TRANSITION_DETERMINATION

OUTCOME_TO_DETERMINATION = {
    v: k
    for k, v in DETERMINATION_TO_OUTCOME.items()
}


def outcome_from_actions(actions):
    outcomes = [TRANSITION_DETERMINATION[action] for action in actions]
    if len(set(outcomes)) != 1:
        raise ValueError('Mixed determination transitions selected - please contact an admin')
    outcome = outcomes[0]
    return OUTCOME_TO_DETERMINATION[outcome]


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
