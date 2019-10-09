from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.db import transaction
from django.db.models import Q, Prefetch
from django.utils import timezone

from wagtail.core.models import Page

from rest_framework import generics, mixins, permissions
from rest_framework.response import Response
from rest_framework.exceptions import (NotFound, PermissionDenied,
                                       ValidationError)
from rest_framework_api_key.permissions import HasAPIKey
from django_filters import rest_framework as filters

from opentech.api.pagination import StandardResultsSetPagination
from opentech.apply.activity.models import Activity, COMMENT
from opentech.apply.activity.messaging import messenger, MESSAGES
from opentech.apply.determinations.views import DeterminationCreateOrUpdateView
from opentech.apply.review.models import Review
from opentech.apply.funds.models import FundType, LabType

from .models import ApplicationSubmission, RoundsAndLabs
from .serializers import (
    CommentSerializer,
    CommentCreateSerializer,
    CommentEditSerializer,
    RoundLabDetailSerializer,
    RoundLabSerializer,
    SubmissionActionSerializer,
    SubmissionListSerializer,
    SubmissionDetailSerializer,
)
from .permissions import IsApplyStaffUser, IsAuthor
from .workflow import PHASES


class RoundLabFilter(filters.ModelChoiceFilter):
    def filter(self, qs, value):
        if not value:
            return qs

        return qs.filter(Q(round=value) | Q(page=value))


class SubmissionsFilter(filters.FilterSet):
    round = RoundLabFilter(queryset=RoundsAndLabs.objects.all())
    status = filters.MultipleChoiceFilter(choices=PHASES)
    active = filters.BooleanFilter(method='filter_active', label='Active')
    submit_date = filters.DateFromToRangeFilter(field_name='submit_time', label='Submit date')
    fund = filters.ModelMultipleChoiceFilter(
        field_name='page', label='fund',
        queryset=Page.objects.type(FundType) | Page.objects.type(LabType)
    )

    class Meta:
        model = ApplicationSubmission
        fields = ('status', 'round', 'active', 'submit_date', 'fund', )

    def filter_active(self, qs, name, value):
        if value is None:
            return qs

        if value:
            return qs.active()
        else:
            return qs.inactive()


class SubmissionList(generics.ListAPIView):
    queryset = ApplicationSubmission.objects.current().with_latest_update()
    serializer_class = SubmissionListSerializer
    permission_classes = (
        HasAPIKey | permissions.IsAuthenticated, HasAPIKey | IsApplyStaffUser,
    )
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = SubmissionsFilter
    pagination_class = StandardResultsSetPagination


class SubmissionDetail(generics.RetrieveAPIView):
    queryset = ApplicationSubmission.objects.all().prefetch_related(
        Prefetch('reviews', Review.objects.submitted()),
    )
    serializer_class = SubmissionDetailSerializer
    permission_classes = (
        permissions.IsAuthenticated, IsApplyStaffUser,
    )


class SubmissionAction(generics.RetrieveAPIView):
    queryset = ApplicationSubmission.objects.all()
    serializer_class = SubmissionActionSerializer
    permission_classes = (
        permissions.IsAuthenticated, IsApplyStaffUser,
    )

    def post(self, request, *args, **kwargs):
        action = request.data.get('action')
        if not action:
            raise ValidationError('Action must be provided.')
        obj = self.get_object()

        redirect = DeterminationCreateOrUpdateView.should_redirect(
            request, obj, action)
        if redirect:
            raise NotFound({
                'detail': 'The action should be performed at the determination view',
                'target': redirect.url,
            })
        try:
            obj.perform_transition(action, self.request.user, request=self.request)
        except DjangoPermissionDenied as e:
            raise PermissionDenied(str(e))
        # refresh_from_db() raises errors for particular actions.
        obj = self.get_object()
        serializer = SubmissionDetailSerializer(obj, context={
            'request': request,
        })
        return Response({
            'id': serializer.data['id'],
            'status': serializer.data['status'],
            'actions': serializer.data['actions'],
            'phase': serializer.data['phase'],
        })


class RoundLabDetail(generics.RetrieveAPIView):
    queryset = RoundsAndLabs.objects.all()
    serializer_class = RoundLabDetailSerializer
    permission_classes = (
        permissions.IsAuthenticated, IsApplyStaffUser,
    )

    def get_object(self):
        return super().get_object().specific


class RoundLabList(generics.ListAPIView):
    queryset = RoundsAndLabs.objects.specific()
    serializer_class = RoundLabSerializer
    permission_classes = (
        permissions.IsAuthenticated, IsApplyStaffUser,
    )
    pagination_class = StandardResultsSetPagination


class NewerThanFilter(filters.ModelChoiceFilter):
    def filter(self, qs, value):
        if not value:
            return qs

        return qs.newer(value)


class CommentFilter(filters.FilterSet):
    since = filters.DateTimeFilter(field_name="timestamp", lookup_expr='gte')
    before = filters.DateTimeFilter(field_name="timestamp", lookup_expr='lte')
    newer = NewerThanFilter(queryset=Activity.comments.all())

    class Meta:
        model = Activity
        fields = ['visibility', 'since', 'before', 'newer']


class AllCommentFilter(CommentFilter):
    class Meta(CommentFilter.Meta):
        fields = CommentFilter.Meta.fields + ['source_object_id']


class CommentList(generics.ListAPIView):
    queryset = Activity.comments.all()
    serializer_class = CommentSerializer
    permission_classes = (
        permissions.IsAuthenticated, IsApplyStaffUser,
    )
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = AllCommentFilter
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return super().get_queryset().visible_to(self.request.user)


class CommentListCreate(generics.ListCreateAPIView):
    queryset = Activity.comments.all().select_related('user')
    serializer_class = CommentCreateSerializer
    permission_classes = (
        permissions.IsAuthenticated, IsApplyStaffUser,
    )
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = CommentFilter
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return super().get_queryset().filter(
            submission=self.kwargs['pk']
        ).visible_to(self.request.user)

    def perform_create(self, serializer):
        obj = serializer.save(
            timestamp=timezone.now(),
            type=COMMENT,
            user=self.request.user,
            source=ApplicationSubmission.objects.get(pk=self.kwargs['pk'])
        )
        messenger(
            MESSAGES.COMMENT,
            request=self.request,
            user=self.request.user,
            source=obj.submission,
            related=obj,
        )


class CommentEdit(
        mixins.RetrieveModelMixin,
        mixins.CreateModelMixin,
        generics.GenericAPIView,
):
    queryset = Activity.comments.all().select_related('user')
    serializer_class = CommentEditSerializer
    permission_classes = (
        permissions.IsAuthenticated, IsAuthor
    )

    def post(self, request, *args, **kwargs):
        return self.edit(request, *args, **kwargs)

    @transaction.atomic
    def edit(self, request, *args, **kwargs):
        comment_to_edit = self.get_object()
        comment_to_update = self.get_object()

        comment_to_edit.previous = comment_to_update
        comment_to_edit.pk = None
        comment_to_edit.edited = timezone.now()

        serializer = self.get_serializer(comment_to_edit, data=request.data)
        serializer.is_valid(raise_exception=True)

        if serializer.validated_data['message'] != comment_to_update.message:
            self.perform_create(serializer)
            comment_to_update.current = False
            comment_to_update.save()
            return Response(serializer.data)

        return Response(self.get_serializer(comment_to_update).data)
