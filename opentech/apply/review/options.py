NA = 99

RATE_CHOICES = (
    (0, '0. Need more info'),
    (1, '1. Poor'),
    (2, '2. Not so good'),
    (3, '3. Is o.k.'),
    (4, '4. Good'),
    (5, '5. Excellent'),
    (NA, 'n/a - choose not to answer'),
)
RATE_CHOICES_DICT = dict(RATE_CHOICES)
RATE_CHOICE_NA = RATE_CHOICES_DICT[NA]

NO = 0
MAYBE = 1
YES = 2

RECOMMENDATION_CHOICES = (
    (NO, 'No'),
    (MAYBE, 'Maybe'),
    (YES, 'Yes'),
)

DISAGREE = 0
AGREE = 1

OPINION_CHOICES = (
    (AGREE, 'Agree'),
    (DISAGREE, 'Disagree'),
)
