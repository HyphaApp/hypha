from rest_framework import generics
from rest_framework import permissions
from django_filters.rest_framework import DjangoFilterBackend

from opentech.api.pagination import StandardResultsSetPagination
from .models import ApplicationSubmission
from .serializers import SubmissionListSerializer, SubmissionDetailSerializer
from .permissions import IsApplyStaffUser


class SubmissionList(generics.ListAPIView):
    queryset = ApplicationSubmission.objects.all()
    serializer_class = SubmissionListSerializer
    permission_classes = (
        permissions.IsAuthenticated, IsApplyStaffUser,
    )
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('round', 'status')
    pagination_class = StandardResultsSetPagination


class SubmissionDetail(generics.RetrieveAPIView):
    queryset = ApplicationSubmission.objects.all()
    serializer_class = SubmissionDetailSerializer
    permission_classes = (
        permissions.IsAuthenticated, IsApplyStaffUser,
    )
