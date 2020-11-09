from rest_framework import exceptions, serializers

from hypha.apply.funds.models import ScreeningStatus


class ScreeningStatusListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScreeningStatus
        fields = ('title', 'yes', 'default')


class ScreeningStatusSerializer(serializers.Serializer):
    title = serializers.CharField()

    def validate_title(self, value):
        try:
            ScreeningStatus.objects.get(title=value)
        except ScreeningStatus.DoesNotExist:
            raise exceptions.ValidationError({
                'detail': 'Title is not valid'
            })
        return value


class ScreeningStatusDefaultSerializer(serializers.Serializer):
    yes = serializers.BooleanField()
