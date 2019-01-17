from rest_framework import serializers

from opentech.apply.activity.models import Activity
from .models import ApplicationSubmission, Round


class SubmissionListSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source='page.title')

    class Meta:
        model = ApplicationSubmission
        fields = ('id', 'title', 'status')


class SubmissionDetailSerializer(serializers.ModelSerializer):
    actions = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(
            queryset=Activity.actions.all()
        )
    )

    class Meta:
        model = ApplicationSubmission
        fields = ('id', 'title', 'actions')


class RoundDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Round
        fields = ('title', )
        # TODO check what statuses are and add statuses list in fields
