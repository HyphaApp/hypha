from django.conf import settings
from django.utils.translation import gettext_lazy as _

NA = 99

DEFAULT_RATE_CHOICES = (
    (0, _("0. Need more info")),
    (1, _("1. Poor")),
    (2, _("2. Not so good")),
    (3, _("3. Is o.k.")),
    (4, _("4. Good")),
    (5, _("5. Excellent")),
    (NA, _("n/a - choose not to answer")),
)


def get_rate_choices():
    """
    Apply the REVIEW_RATE_CHOICES setting to DEFAULT_RATE_CHOICES.

    The setting maps a score value (int or str) to a new label, or to a falsy
    value to disable that choice.

    Returns ``(choices, labels)`` where ``labels`` also includes disabled
    choices, so existing reviews using them can still be displayed.
    """
    overrides = {
        str(key): value
        for key, value in getattr(settings, "REVIEW_RATE_CHOICES", {}).items()
    }
    choices = []
    labels = {}
    for value, default_label in DEFAULT_RATE_CHOICES:
        override = overrides.get(str(value), default_label)
        label = override if isinstance(override, str) and override else default_label
        labels[value] = label
        if override:
            choices.append((value, label))
    return tuple(choices), labels


RATE_CHOICES, RATE_CHOICES_DICT = get_rate_choices()
RATE_CHOICE_NA = RATE_CHOICES_DICT[NA]

NO = 0
MAYBE = 1
YES = 2

RECOMMENDATION_CHOICES = (
    (NO, _("No")),
    (MAYBE, _("Maybe")),
    (YES, _("Yes")),
)

DISAGREE = 0
AGREE = 1

OPINION_CHOICES = (
    (AGREE, _("Agree")),
    (DISAGREE, _("Disagree")),
)

PRIVATE = "private"
REVIEWER = "reviewers"

VISIBILITY_HELP_TEXT = {
    PRIVATE: _("Visible only to staff."),
    REVIEWER: _("Visible to other reviewers and staff."),
}

VISIBILITY = {
    PRIVATE: _("Private"),
    REVIEWER: _("Reviewers and Staff"),
}
