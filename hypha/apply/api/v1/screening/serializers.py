from rest_framework import exceptions, serializers

from hypha.apply.funds.models import ScreeningStatus


class ScreeningStatusListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScreeningStatus
        fields = ("id", "title", "yes", "default")


class ScreeningStatusSerializer(serializers.Serializer):
    id = serializers.IntegerField()

    def validate_id(self, value):
        try:
            ScreeningStatus.objects.get(id=value)
        except ScreeningStatus.DoesNotExist as e:
            raise exceptions.ValidationError({"detail": "Not found"}) from e
        return value


class ScreeningStatusDefaultSerializer(serializers.Serializer):
    yes = serializers.BooleanField()
