from rest_framework import serializers

from hypha.apply.determinations.models import Determination


class SubmissionDeterminationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Determination
        fields = [
            "id",
            "is_draft",
        ]
        extra_kwargs = {
            "is_draft": {"required": False},
        }

    def validate(self, data):
        validated_data = super().validate(data)
        validated_data["form_data"] = dict(validated_data.items())
        return validated_data

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        instance.send_notice = (
            self.validated_data[instance.send_notice_field.id]
            if instance.send_notice_field
            else True
        )
        message = self.validated_data[instance.message_field.id]
        instance.message = "" if message is None else message
        try:
            instance.outcome = int(self.validated_data[instance.determination_field.id])
            # Need to catch KeyError as outcome field would not exist in case of edit.
        except KeyError:
            pass
        instance.is_draft = self.validated_data.get("is_draft", False)
        instance.form_data = self.validated_data["form_data"]
        instance.save()
        return instance
