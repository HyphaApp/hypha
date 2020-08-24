from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey

from hypha.apply.activity.messaging import MESSAGES, messenger
from hypha.apply.funds.models import AssignedReviewers
from hypha.apply.review.models import Review, ReviewOpinion
from hypha.apply.stream_forms.models import BaseStreamForm

from ..mixin import SubmissionNestedMixin
from ..permissions import IsApplyStaffUser
from ..stream_serializers import WagtailSerializer
from .permissions import (
    HasReviewCreatePermission,
    HasReviewDeletePermission,
    HasReviewDetialPermission,
    HasReviewEditPermission,
    HasReviewOpinionPermission,
)
from .serializers import (
    FieldSerializer,
    ReviewOpinionWriteSerializer,
    SubmissionReviewDetailSerializer,
    SubmissionReviewSerializer,
)
from .utils import get_review_form_fields_for_stage, review_workflow_actions


class SubmissionReviewViewSet(
    BaseStreamForm,
    WagtailSerializer,
    SubmissionNestedMixin,
    viewsets.GenericViewSet
):
    permission_classes = (
        HasAPIKey | permissions.IsAuthenticated, HasAPIKey | IsApplyStaffUser,
    )
    permission_classes_by_action = {
        'create': [permissions.IsAuthenticated, HasReviewCreatePermission, ],
        'retrieve': [permissions.IsAuthenticated, HasReviewDetialPermission, ],
        'update': [permissions.IsAuthenticated, HasReviewEditPermission, ],
        'delete': [permissions.IsAuthenticated, HasReviewDeletePermission, ],
        'opinions': [permissions.IsAuthenticated, HasReviewOpinionPermission, ],
        'fields': [permissions.IsAuthenticated, HasReviewCreatePermission, ],
    }
    serializer_class = SubmissionReviewSerializer

    def get_permissions(self):
        try:
            # return permission_classes depending on `action`
            return [permission() for permission in self.permission_classes_by_action[self.action]]
        except KeyError:
            # action is not set return default permission_classes
            return [permission() for permission in self.permission_classes]

    def get_defined_fields(self):
        submission = self.get_submission_object()
        if self.action in ['retrieve', 'update', 'opinions']:
            # For detail and edit api form fields used while submitting
            # review should be used.
            review = self.get_object()
            return review.form_fields
        return get_review_form_fields_for_stage(submission)

    def get_object(self):
        obj = get_object_or_404(Review, id=self.kwargs['pk'])
        self.check_object_permissions(self.request, obj)
        return obj

    def get_queryset(self):
        submission = self.get_submission_object()
        return Review.objects.filter(submission=submission, is_draft=False)

    def get_reviewer(self):
        submission = self.get_submission_object()
        ar, _ = AssignedReviewers.objects.get_or_create_for_user(
            submission=submission,
            reviewer=self.request.user,
        )
        return ar

    def create(self, request, *args, **kwargs):
        submission = self.get_submission_object()
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        instance = ser.Meta.model.objects.create(
            form_fields=self.get_defined_fields(),
            submission=submission, author=self.get_reviewer()
        )
        instance.save()
        ser.update(instance, ser.validated_data)
        if not instance.is_draft:
            messenger(
                MESSAGES.NEW_REVIEW,
                request=self.request,
                user=self.request.user,
                source=submission,
                related=instance,
            )
            # Automatic workflow actions.
            review_workflow_actions(self.request, submission)
        ser = self.get_serializer(instance)
        return Response(ser.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        """Get details of a review on a submission"""
        review = self.get_object()
        review_data = review.form_data
        review_data['id'] = review.id
        review_data['score'] = review.score
        review_data['opinions'] = review.opinions
        ser = self.get_serializer(review_data)
        return Response(ser.data)

    def update(self, request, *args, **kwargs):
        review = self.get_object()
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.update(review, ser.validated_data)

        messenger(
            MESSAGES.EDIT_REVIEW,
            user=self.request.user,
            request=self.request,
            source=review.submission,
            related=review,
        )
        # Automatic workflow actions.
        review_workflow_actions(self.request, review.submission)
        ser = SubmissionReviewDetailSerializer(review)
        ser = self.get_serializer(review)
        return Response(ser.data)

    """
    Commenting out this api as it is not used in frontend for now.
    We can discuss and implement review list view in frontend later on.

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        ser = SubmissionReviewDetailSerializer(queryset, many=True)
        return Response(ser.data)
    """

    def destroy(self, request, *args, **kwargs):
        """Delete a review on a submission"""
        review = self.get_object()
        messenger(
            MESSAGES.DELETE_REVIEW,
            user=request.user,
            request=request,
            source=review.submission,
            related=review,
        )
        review.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def fields(self, request, *args, **kwargs):
        fields = self.get_form_fields()
        fields = FieldSerializer(fields.items(), many=True)
        return Response(fields.data)

    @action(detail=True, methods=['post'])
    def opinions(self, request, *args, **kwargs):
        review = self.get_object()
        ser = ReviewOpinionWriteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        opinion = ser.validated_data['opinion']
        try:
            review_opinion = ReviewOpinion.objects.get(
                review=review,
                author=self.get_reviewer()
            )
        except ReviewOpinion.DoesNotExist:
            ReviewOpinion.objects.create(
                review=review,
                author=self.get_reviewer(),
                opinion=opinion
            )
        else:
            review_opinion.opinion = opinion
            review_opinion.save()
        review_data = review.form_data
        review_data['id'] = review.id
        review_data['score'] = review.score
        review_data['opinions'] = review.opinions
        ser = self.get_serializer(review_data)
        return Response(ser.data, status=status.HTTP_201_CREATED)
