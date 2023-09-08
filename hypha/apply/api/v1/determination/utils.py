from django.utils.translation import gettext as _

from hypha.apply.determinations.options import (
    DETERMINATION_CHOICES,
    TRANSITION_DETERMINATION,
)
from hypha.apply.determinations.utils import determination_actions


def get_fields_for_stage(submission):
    forms = submission.get_from_parent("determination_forms").all()
    index = submission.workflow.stages.index(submission.stage)
    try:
        return forms[index].form.form_fields
    except IndexError:
        return forms[0].form.form_fields


def outcome_choices_for_phase(submission, user):
    """
    Outcome choices correspond to Phase transitions.
    We need to filter out non-matching choices.
    i.e. a transition to In Review is not a determination, while Needs more info or Rejected are.
    """
    available_choices = [("", _("-- No determination selected -- "))]
    choices = dict(DETERMINATION_CHOICES)
    for transition_name in determination_actions(user, submission):
        try:
            determination_type = TRANSITION_DETERMINATION[transition_name]
        except KeyError:
            pass
        else:
            available_choices.append((determination_type, choices[determination_type]))
    return available_choices
