import django_filters

from .models import Activity


class NotificationFilter(django_filters.FilterSet):

    class Meta:
        model = Activity
        fields = {
            'timestamp',
            'source_content_type',
        }
