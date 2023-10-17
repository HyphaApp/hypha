from .options import DETERMINATION_TO_OUTCOME, TRANSITION_DETERMINATION

OUTCOME_TO_DETERMINATION = {v: k for k, v in DETERMINATION_TO_OUTCOME.items()}


def outcome_from_actions(actions):
    outcomes = [TRANSITION_DETERMINATION[action] for action in actions]
    if len(set(outcomes)) != 1:
        raise ValueError(
            "Mixed determination transitions selected - please contact an admin"
        )
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


def has_final_determination(submission):
    return submission.determinations.final().exists()
