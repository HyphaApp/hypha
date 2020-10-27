from django.shortcuts import get_object_or_404

from rest_framework import viewsets, permissions, mixins, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action

from django_filters import rest_framework as filters

from rest_framework_api_key.permissions import HasAPIKey

from hypha.apply.funds.models import ScreeningStatus

from ..pagination import StandardResultsSetPagination
from ..permissions import IsApplyStaffUser
from ..mixin import SubmissionNestedMixin

from .filters import ScreeningStatusFilter
from .serializers import (
    ScreeningStatusListSerializer,
    ScreeningStatusSerializer,
    ScreeningStatusDefaultSerializer
)


class ScreeningStatusViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (
        HasAPIKey | permissions.IsAuthenticated, HasAPIKey | IsApplyStaffUser,
    )
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = ScreeningStatusFilter
    pagination_class = StandardResultsSetPagination
    queryset = ScreeningStatus.objects.all()
    serializer_class = ScreeningStatusListSerializer


class SubmissionScreeningStatusViewSet(
    SubmissionNestedMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet
):
    permission_classes = (
        HasAPIKey | permissions.IsAuthenticated, HasAPIKey | IsApplyStaffUser,
    )
    serializer_class = ScreeningStatusSerializer

    def get_queryset(self):
        submission = self.get_submission_object()
        return submission.screening_statuses.all()

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        submission = self.get_submission_object()
        screening_status = get_object_or_404(
            ScreeningStatus, title=ser.validated_data['title']
        )
        if not submission.screening_statuses.filter(default=True).exists():
            raise ValidationError({'detail': "Can't set screening status without default being set"})
        if (
            submission.screening_statuses.exists() and
            submission.screening_statuses.first().yes != screening_status.yes
        ):
            raise ValidationError({'detail': "Can't set screening status for both yes and no"})
        submission.screening_statuses.add(
            screening_status
        )
        return Response(status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def default(self, request, *args, **kwargs):
        ser = ScreeningStatusDefaultSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        yes = ser.validated_data['yes']
        submission = self.get_submission_object()
        if submission.screening_statuses.filter(default=False).exists():
            raise ValidationError({
                'detail': "Can't set default as more than one screening status is already set."
            })
        screening_status = ScreeningStatus.objects.get(default=True, yes=yes)
        if submission.has_default_screening_status_set:
            default_status = submission.screening_statuses.get()
            submission.screening_statuses.remove(default_status)
        submission.screening_statuses.add(screening_status)
        ser = self.get_serializer(submission.screening_statuses.get(default=True))
        return Response(ser.data, status=status.HTTP_201_CREATED)
