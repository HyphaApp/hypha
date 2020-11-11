from rest_framework import exceptions, serializers

from hypha.apply.funds.models import ScreeningStatus


class ScreeningStatusListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScreeningStatus
        fields = ('id', 'title', 'yes', 'default')


class ScreeningStatusSerializer(serializers.Serializer):
    id = serializers.IntegerField()

    def validate_id(self, value):
        try:
            ScreeningStatus.objects.get(id=value)
        except ScreeningStatus.DoesNotExist:
            raise exceptions.ValidationError({
                'detail': 'Not found'
            })
        return value


class ScreeningStatusDefaultSerializer(serializers.Serializer):
    yes = serializers.BooleanField()
