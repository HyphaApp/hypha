from datetime import timedelta

import django_filters
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django_filters.filters import DateRangeFilter, _truncate

from .models import Activity


class NotificationFilter(django_filters.FilterSet):
    timestamp_choices = [
        ("today", _("Today")),
        ("yesterday", _("Yesterday")),
        ("week", _("Past 7 days")),
        ("month", _("This month")),
    ]
    timestamp_filters = {
        "today": lambda qs, name: qs.filter(
            **{
                "%s__year" % name: now().year,
                "%s__month" % name: now().month,
                "%s__day" % name: now().day,
            }
        ),
        "yesterday": lambda qs, name: qs.filter(
            **{
                "%s__year" % name: (now() - timedelta(days=1)).year,
                "%s__month" % name: (now() - timedelta(days=1)).month,
                "%s__day" % name: (now() - timedelta(days=1)).day,
            }
        ),
        "week": lambda qs, name: qs.filter(
            **{
                "%s__gte" % name: _truncate(now() - timedelta(days=7)),
                "%s__lt" % name: _truncate(now() + timedelta(days=1)),
            }
        ),
        "month": lambda qs, name: qs.filter(
            **{"%s__year" % name: now().year, "%s__month" % name: now().month}
        ),
    }

    date = DateRangeFilter(
        field_name="timestamp", choices=timestamp_choices, filters=timestamp_filters
    )

    class Meta:
        model = Activity
        fields = {}
