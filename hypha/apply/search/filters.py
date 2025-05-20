import datetime as dt

from django.db.models import Q

from hypha.apply.search.query_parser import tokenize_date_filter_value


def apply_date_filter(qs, field, values):
    """Given a queryset, a field name, and a list of date strings, filter the queryset."""
    q_obj = Q()

    for date_str in values:
        tokens = tokenize_date_filter_value(date_str)

        if q := date_filter_tokens_to_q_obj(tokens=tokens, field=field):
            q_obj &= q

    return qs.filter(q_obj)


def date_filter_tokens_to_q_obj(tokens: list, field: str) -> Q:
    """Convert a date tokens parsed using `tokenize_date_filter_value` into a
    Q object that can be used to filter a queryset.

    Args:
    - tokens: A list of tokens parsed using `tokenize_date_filter_value`.
    - field: This should be the name of a DateTimeField.
    """
    match tokens:
        case [operator, year, month, day]:
            if operator == ">=":
                return Q(**{f"{field}__date__gte": dt.date(year, month, day)})
            elif operator == "<=":
                return Q(**{f"{field}__date__lte": dt.date(year, month, day)})
            elif operator == ">":
                return Q(**{f"{field}__date__gt": dt.date(year, month, day)})
            elif operator == "<":
                return Q(**{f"{field}__date__lt": dt.date(year, month, day)})
            elif operator == "=":
                return Q(**{f"{field}__date": dt.date(year, month, day)})
            else:
                return Q(**{f"{field}__date": dt.date(year, month, day)})
        case [operator, year, month]:
            if operator == ">=":
                return Q(**{f"{field}__year__gte": year, f"{field}__month__gte": month})
            elif operator == "<=":
                return Q(**{f"{field}__year__lte": year, f"{field}__month__lte": month})
            elif operator == ">":
                return Q(**{f"{field}__year__gt": year, f"{field}__month__gt": month})
            elif operator == "<":
                return Q(**{f"{field}__year__lt": year, f"{field}__month__lt": month})
            elif operator == "=":
                return Q(**{f"{field}__year": year, f"{field}__month": month})
            else:
                return Q(**{f"{field}__year": year, f"{field}__month": month})
        case [operator, year]:
            if operator == ">=":
                return Q(**{f"{field}__year__gte": year})
            elif operator == "<=":
                return Q(**{f"{field}__year__lte": year})
            elif operator == ">":
                return Q(**{f"{field}__year__gt": year})
            elif operator == "<":
                return Q(**{f"{field}__year__lt": year})
            elif operator == "=":
                return Q(**{f"{field}__year": year})
            else:
                return Q(**{f"{field}__year": year})
    return Q()
