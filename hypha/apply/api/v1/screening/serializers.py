from rest_framework import serializers

from hypha.apply.funds.models import ScreeningStatus


class ScreeningStatusListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScreeningStatus
        fields = ('title', 'yes', 'default')


class ScreeningStatusSerializer(serializers.Serializer):
    title = serializers.CharField()


class ScreeningStatusDefaultSerializer(serializers.Serializer):
    yes = serializers.BooleanField()
