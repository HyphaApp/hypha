from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.db import transaction
from django.db.models import Prefetch
from django.utils import timezone
from django_filters import rest_framework as filters
from rest_framework import mixins, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey

from hypha.apply.activity.messaging import MESSAGES, messenger
from hypha.apply.activity.models import COMMENT, Activity
from hypha.apply.determinations.views import DeterminationCreateOrUpdateView
from hypha.apply.funds.models import ApplicationSubmission, RoundsAndLabs
from hypha.apply.review.models import Review

from .filters import CommentFilter, SubmissionsFilter
from .mixin import SubmissionNestedMixin
from .pagination import StandardResultsSetPagination
from .permissions import IsApplyStaffUser, IsAuthor
from .serializers import (
    CommentCreateSerializer,
    CommentEditSerializer,
    CommentSerializer,
    RoundLabDetailSerializer,
    RoundLabSerializer,
    SubmissionActionSerializer,
    SubmissionDetailSerializer,
    SubmissionListSerializer,
)


class SubmissionViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (
        HasAPIKey | permissions.IsAuthenticated, HasAPIKey | IsApplyStaffUser,
    )
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = SubmissionsFilter
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        if self.action == 'list':
            return SubmissionListSerializer
        return SubmissionDetailSerializer

    def get_queryset(self):
        if self.action == 'list':
            return ApplicationSubmission.objects.current().with_latest_update()
        return ApplicationSubmission.objects.all().prefetch_related(
            Prefetch('reviews', Review.objects.submitted()),
        )


class SubmissionActionViewSet(
    SubmissionNestedMixin,
    viewsets.GenericViewSet
):
    serializer_class = SubmissionActionSerializer
    permission_classes = (
        permissions.IsAuthenticated, IsApplyStaffUser,
    )

    def get_object(self):
        return self.get_submission_object()

    def list(self, request, *args, **kwargs):
        """
        List all the actions that can be taken on a submission.

        E.g. All the states this submission can be transistion to.
        """
        obj = self.get_object()
        ser = self.get_serializer(obj)
        return Response(ser.data)

    def create(self, request, *args, **kwargs):
        """
        Transistion a submission from one state to other.

        E.g. To transition a submission from `Screening` to `Internal Review`
        following post data can be used:

        ```
        {"action": "internal_review"}
        ```
        """
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


class RoundViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    queryset = RoundsAndLabs.objects.specific()
    serializer_class = RoundLabSerializer
    permission_classes = (
        permissions.IsAuthenticated, IsApplyStaffUser,
    )
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        if self.action == 'list':
            return RoundLabSerializer
        return RoundLabDetailSerializer


class SubmissionCommentViewSet(
    SubmissionNestedMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet
):
    """
    List all the comments on a submission.
    """
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
            submission=self.get_submission_object()
        ).visible_to(self.request.user)

    def perform_create(self, serializer):
        """
        Add a comment on a submission.
        """
        obj = serializer.save(
            timestamp=timezone.now(),
            type=COMMENT,
            user=self.request.user,
            source=self.get_submission_object()
        )
        messenger(
            MESSAGES.COMMENT,
            request=self.request,
            user=self.request.user,
            source=obj.source,
            related=obj,
        )


class CommentViewSet(
        mixins.ListModelMixin,
        viewsets.GenericViewSet,
):
    """
    Edit a comment.
    """
    queryset = Activity.comments.all().select_related('user')
    serializer_class = CommentEditSerializer
    permission_classes = (
        permissions.IsAuthenticated, IsAuthor
    )

    def get_serializer_class(self):
        if self.action == 'list':
            return CommentSerializer
        return CommentEditSerializer

    def get_queryset(self):
        return super().get_queryset().visible_to(self.request.user)

    @action(detail=True, methods=['post'])
    def edit(self, request, *args, **kwargs):
        return self.edit_comment(request, *args, **kwargs)

    @transaction.atomic
    def edit_comment(self, request, *args, **kwargs):
        comment_to_edit = self.get_object()
        comment_to_update = self.get_object()

        comment_to_edit.previous = comment_to_update
        comment_to_edit.pk = None
        comment_to_edit.edited = timezone.now()

        serializer = self.get_serializer(comment_to_edit, data=request.data)
        serializer.is_valid(raise_exception=True)

        if (serializer.validated_data['message'] != comment_to_update.message) or (serializer.validated_data['visibility'] != comment_to_update.visibility):
            self.perform_create(serializer)
            comment_to_update.current = False
            comment_to_update.save()
            return Response(serializer.data)

        return Response(self.get_serializer(comment_to_update).data)

    def perform_create(self, serializer):
        serializer.save()
