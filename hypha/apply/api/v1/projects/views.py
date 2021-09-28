from django.shortcuts import get_object_or_404
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey

from hypha.apply.projects.models.payment import InvoiceDeliverable
from hypha.apply.projects.models.project import Deliverable

from ..mixin import InvoiceNestedMixin, ProjectNestedMixin
from ..permissions import IsApplyStaffUser
from .serializers import DeliverableSerializer, InvoiceDeliverableListSerializer


class DeliverableViewSet(
    InvoiceNestedMixin,
    ProjectNestedMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    permission_classes = (
        HasAPIKey | permissions.IsAuthenticated, HasAPIKey | IsApplyStaffUser,
    )
    serializer_class = InvoiceDeliverableListSerializer
    pagination_class = None

    def get_queryset(self):
        invoice = self.get_invoice_object()
        return invoice.deliverables.all()

    def create(self, request, *args, **kwargs):
        ser = DeliverableSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        project = self.get_project_object()
        deliverable_id = ser.validated_data['id']
        if not project.deliverables.filter(id=deliverable_id).exists():
            raise ValidationError({'detail': "Not Found"})
        invoice = self.get_invoice_object()
        deliverable = get_object_or_404(
            Deliverable, id=deliverable_id
        )
        if invoice.deliverables.filter(deliverable=deliverable).exists():
            raise ValidationError({'detail': "Invoice Already has this deliverable"})
        quantity = ser.validated_data['quantity']
        if deliverable.available_to_invoice < quantity:
            raise ValidationError({'detail': "Required quantity is more than available"})
        invoice_deliverable = InvoiceDeliverable.objects.create(
            deliverable=deliverable,
            quantity=ser.validated_data['quantity']
        )
        invoice.deliverables.add(invoice_deliverable)
        ser = self.get_serializer(invoice.deliverables.all(), many=True)
        return Response(
            {'deliverables': ser.data, 'total': invoice.deliverables_total_amount['total']},
            status=status.HTTP_201_CREATED
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["invoice"] = self.get_invoice_object()
        return context

    def destroy(self, request, *args, **kwargs):
        deliverable = self.get_object()
        invoice = self.get_invoice_object()
        invoice.deliverables.remove(deliverable)
        ser = self.get_serializer(invoice.deliverables.all(), many=True)
        return Response(
            {'deliverables': ser.data, 'total': invoice.deliverables_total_amount['total']},
        )
