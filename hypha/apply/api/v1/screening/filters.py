from django_filters import rest_framework as filters

from hypha.apply.funds.models import ScreeningStatus


class ScreeningStatusFilter(filters.FilterSet):
    class Meta:
        model = ScreeningStatus
        fields = ["yes", "default"]
