from rest_framework import exceptions, serializers

from hypha.apply.projects.models import InvoiceDeliverable, Deliverable


class InvoiceDeliverableListSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceDeliverable
        fields = ('deliverable', 'quantity')
        depth = 1


class DeliverableSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, default=1)

    def validate_id(self, value):
        try:
            Deliverable.objects.get(id=value)
        except Deliverable.DoesNotExist:
            raise exceptions.ValidationError({
                'detail': 'Not found'
            })
        return value
