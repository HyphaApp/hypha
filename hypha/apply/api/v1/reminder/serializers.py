from rest_framework import serializers

from hypha.apply.funds.models import Reminder


class SubmissionReminderSerializer(serializers.ModelSerializer):

    def validate(self, data):
        """
        Check title & assign are not empty.
        """
        required_fields = ['title', 'assign']
        for field in required_fields:
            if not data.get(field, None):
                raise serializers.ValidationError({field: "shouldn't be empty"})
        return data

    class Meta:
        model = Reminder
        fields = ('time', 'action_type', 'is_expired', 'id', 'action', 'title', 'assign', 'description')
        read_only_fields = ('action_type', 'is_expired')
