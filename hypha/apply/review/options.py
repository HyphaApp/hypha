from django.conf import settings
from django.utils.translation import gettext as _

NA = 99


def get_rate_choices(choices):
    rate_choices = [(i, _("{}. {}".format(i, s))) for i, s in enumerate(choices)]
    rate_choices.append((NA, _("n/a - choose not to answer")))

    return rate_choices


RATE_CHOICES = tuple(get_rate_choices(settings.RATE_CHOICES))
RATE_CHOICES_DICT = dict(RATE_CHOICES)
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

VISIBILILTY_HELP_TEXT = {
    PRIVATE: _("Visible only to staff."),
    REVIEWER: _("Visible to other reviewers and staff."),
}

VISIBILITY = {
    PRIVATE: _("Private"),
    REVIEWER: _("Reviewers and Staff"),
}
