from django.utils.translation import gettext as _

NA = 99

RATE_CHOICES = (
    (0, _('0. Need more info')),
    (1, _('1. Poor')),
    (2, _('2. Not so good')),
    (3, _('3. Is o.k.')),
    (4, _('4. Good')),
    (5, _('5. Excellent')),
    (NA, _('n/a - choose not to answer')),
)

RATE_CHOICES_DICT = dict(RATE_CHOICES)
RATE_CHOICE_NA = RATE_CHOICES_DICT[NA]

NO = 0
MAYBE = 1
YES = 2

RECOMMENDATION_CHOICES = (
    (NO, _('No')),
    (MAYBE, _('Maybe')),
    (YES, _('Yes')),
)

DISAGREE = 0
AGREE = 1

OPINION_CHOICES = (
    (AGREE, _('Agree')),
    (DISAGREE, _('Disagree')),
)

PRIVATE = 'private'
REVIEWER = 'reviewers'

VISIBILILTY_HELP_TEXT = {
    PRIVATE: _('Visible only to staff.'),
    REVIEWER: _('Visible to other reviewers and staff.'),
}

VISIBILITY = {
    PRIVATE: _('Private'),
    REVIEWER: _('Reviewers and Staff'),
}
