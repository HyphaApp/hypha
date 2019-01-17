from rest_framework import generics
from rest_framework import permissions
from django_filters.rest_framework import DjangoFilterBackend

from .models import ApplicationSubmission, Round
from .serializers import SubmissionListSerializer, SubmissionDetailSerializer, RoundDetailSerializer
from .permissions import IsApplyStaffUser


class SubmissionList(generics.ListAPIView):
    queryset = ApplicationSubmission.objects.all()
    serializer_class = SubmissionListSerializer
    permission_classes = (
        permissions.IsAuthenticated, IsApplyStaffUser,
    )
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('round', 'status')


class SubmissionDetail(generics.RetrieveAPIView):
    queryset = ApplicationSubmission.objects.all()
    serializer_class = SubmissionDetailSerializer
    permission_classes = (
        permissions.IsAuthenticated, IsApplyStaffUser,
    )


class RoundList(generics.ListAPIView):
    queryset = Round.objects.all()
    serializer_class = RoundDetailSerializer
    permission_classes = (
        permissions.IsAuthenticated, IsApplyStaffUser,
    )


class RoundDetail(generics.RetrieveAPIView):
    queryset = Round.objects.all()
    serializer_class = RoundDetailSerializer
    permission_classes = (
        permissions.IsAuthenticated, IsApplyStaffUser,
    )
