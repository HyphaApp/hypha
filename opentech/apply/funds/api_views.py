from django.db.models import Q
from rest_framework import generics
from rest_framework import permissions
from django_filters import rest_framework as filters

from wagtail.core.models import Page

from opentech.api.pagination import StandardResultsSetPagination
from opentech.apply.activity.models import Activity
from .models import ApplicationSubmission
from .models.applications import SubmittableStreamForm
from .serializers import (
    CommentSerializer,
    RoundLabSerializer,
    SubmissionListSerializer,
    SubmissionDetailSerializer,
)
from .permissions import IsApplyStaffUser


class RoundLabFilter(filters.ModelChoiceFilter):
    def filter(self, qs, value):
        if not value:
            return qs

        return qs.filter(Q(round=value) | Q(page=value))


class SubmissionsFilter(filters.FilterSet):
    # TODO replace with better call to Round and Lab base class
    round = RoundLabFilter(queryset=Page.objects.type(SubmittableStreamForm))

    class Meta:
        model = ApplicationSubmission
        fields = ('status', 'round')


class SubmissionList(generics.ListAPIView):
    queryset = ApplicationSubmission.objects.current()
    serializer_class = SubmissionListSerializer
    permission_classes = (
        permissions.IsAuthenticated, IsApplyStaffUser,
    )
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = SubmissionsFilter
    pagination_class = StandardResultsSetPagination


class SubmissionDetail(generics.RetrieveAPIView):
    queryset = ApplicationSubmission.objects.all()
    serializer_class = SubmissionDetailSerializer
    permission_classes = (
        permissions.IsAuthenticated, IsApplyStaffUser,
    )


class RoundLabDetail(generics.RetrieveAPIView):
    # TODO replace with better call to Round and Lab base class
    queryset = Page.objects.type(SubmittableStreamForm)
    serializer_class = RoundLabSerializer
    permission_classes = (
        permissions.IsAuthenticated, IsApplyStaffUser,
    )

    def get_object(self):
        return super().get_object().specific


class CommentList(generics.ListAPIView):
    queryset = Activity.comments.all()
    serializer_class = CommentSerializer
    permission_classes = (
        permissions.IsAuthenticated, IsApplyStaffUser,
    )
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('submission', 'visibility')
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return super().get_queryset().visible_to(self.request.user)
