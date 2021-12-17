from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions, serializers

from hypha.apply.projects.models import Deliverable, InvoiceDeliverable


class InvoiceDeliverableListSerializer(serializers.ModelSerializer):
    invoice_id = serializers.SerializerMethodField()
    project_id = serializers.IntegerField(source='deliverable.project.id')

    class Meta:
        model = InvoiceDeliverable
        fields = ('id', 'deliverable', 'quantity', 'invoice_id', 'project_id')
        depth = 1

    def get_invoice_id(self, obj):
        return self.context['invoice'].id


class DeliverableSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, default=1)

    def validate_id(self, value):
        try:
            Deliverable.objects.get(id=value)
        except Deliverable.DoesNotExist:
            raise exceptions.ValidationError({
                'detail': _('Not found')
            })
        return value
