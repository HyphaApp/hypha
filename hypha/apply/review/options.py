from django.utils.translation import gettext as _

NA = 99

RATE_CHOICES = (
    (0, _("0. Not applicable")),
    (1, _("1. Has little merit, relevance to the program objectives")),
    (2, _("2. Has some merit but unlikely to succeed / meet its own and Breakout program's objectives")),
    (3, _("3. Has merit if they can positively adapt the proposal according to my feedback")),
    (4, _("4. Let's support this provided they can answer a few clarifying questions")),
    (5, _("5. Perfect as is, proceed!")),
    (NA, _("n/a - choose not to answer")),
)

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

VISIBILITY_HELP_TEXT = {
    PRIVATE: _("Visible only to staff."),
    REVIEWER: _("Visible to other reviewers and staff."),
}

VISIBILITY = {
    PRIVATE: _("Private"),
    REVIEWER: _("Reviewers and Staff"),
}
