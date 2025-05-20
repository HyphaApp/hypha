import datetime as dt

import pytest
from django.db.models import Q

from ..filters import date_filter_tokens_to_q_obj


@pytest.mark.parametrize(
    "tokens, field, expected",
    [
        (
            [">", 2023, 12, 2],
            "date_field",
            Q(date_field__date__gt=dt.date(2023, 12, 2)),
        ),
        (
            [">=", 2023, 12, 2],
            "date_field",
            Q(date_field__date__gte=dt.date(2023, 12, 2)),
        ),
        (
            ["<=", 2023, 12, 2],
            "date_field",
            Q(date_field__date__lte=dt.date(2023, 12, 2)),
        ),
        ([None, 2023, 12, 2], "date_field", Q(date_field__date=dt.date(2023, 12, 2))),
        (
            [None, 2023, 12],
            "date_field",
            Q(date_field__month=12) & Q(date_field__year=2023),
        ),
        (
            [">", 2023, 12],
            "date_field",
            Q(date_field__month__gt=12) & Q(date_field__year__gt=2023),
        ),
        ([">", 2023], "date_field", Q(date_field__year__gt=2023)),
        (["<", 2023], "date_field", Q(date_field__year__lt=2023)),
        ([None, 2023], "date_field", Q(date_field__year=2023)),
        ([None, 2023], "date_field", Q(date_field__year=2023)),
        ([], "date_field", Q()),
        ([], "date_field", Q()),
    ],
)
def test_date_filter_tokens_to_q_obj(tokens, field, expected):
    assert date_filter_tokens_to_q_obj(tokens=tokens, field=field) == expected
