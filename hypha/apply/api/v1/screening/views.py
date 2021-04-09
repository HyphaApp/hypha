from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey

from hypha.apply.funds.models import ScreeningStatus

from ..mixin import SubmissionNestedMixin
from ..permissions import IsApplyStaffUser
from .filters import ScreeningStatusFilter
from .serializers import (
    ScreeningStatusDefaultSerializer,
    ScreeningStatusListSerializer,
    ScreeningStatusSerializer,
)


class ScreeningStatusViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (
        HasAPIKey | permissions.IsAuthenticated, HasAPIKey | IsApplyStaffUser,
    )
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = ScreeningStatusFilter
    pagination_class = None
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
    serializer_class = ScreeningStatusListSerializer
    pagination_class = None

    def get_queryset(self):
        submission = self.get_submission_object()
        return submission.screening_statuses.all()

    def create(self, request, *args, **kwargs):
        ser = ScreeningStatusSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        submission = self.get_submission_object()
        screening_status = get_object_or_404(
            ScreeningStatus, id=ser.validated_data['id']
        )
        if not submission.screening_statuses.filter(default=True).exists():
            raise ValidationError({'detail': "Can't set Screening decision without default being set"})
        if (
            submission.screening_statuses.exists() and
            submission.screening_statuses.first().yes != screening_status.yes
        ):
            raise ValidationError({'detail': "Can't set Screening decision for both yes and no"})
        submission.screening_statuses.add(
            screening_status
        )
        ser = self.get_serializer(submission.screening_statuses.all(), many=True)
        return Response(ser.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def default(self, request, *args, **kwargs):
        ser = ScreeningStatusDefaultSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        yes = ser.validated_data['yes']
        submission = self.get_submission_object()
        if submission.screening_statuses.filter(default=False).exists():
            submission.screening_statuses.remove(*submission.screening_statuses.filter(default=False))
        screening_status = ScreeningStatus.objects.get(default=True, yes=yes)
        if submission.has_default_screening_status_set:
            default_status = submission.screening_statuses.get()
            submission.screening_statuses.remove(default_status)
        submission.screening_statuses.add(screening_status)
        ser = self.get_serializer(submission.screening_statuses.get(default=True))
        return Response(ser.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        screening_status = self.get_object()
        if screening_status.default:
            raise ValidationError({
                'detail': "Can't delete default Screening decision."
            })
        submission = self.get_submission_object()
        submission.screening_statuses.remove(screening_status)
        ser = self.get_serializer(submission.screening_statuses.all(), many=True)
        return Response(ser.data)
