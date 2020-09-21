from django.shortcuts import get_object_or_404

from rest_framework import (
    mixins, viewsets,
    permissions, status,
)
from rest_framework.response import Response
from rest_framework.decorators import action

from rest_framework_api_key.permissions import HasAPIKey

from hypha.apply.activity.messaging import MESSAGES, messenger
from hypha.apply.review.models import Review, ReviewOpinion
from hypha.apply.funds.models import AssignedReviewers
from hypha.apply.stream_forms.models import BaseStreamForm

from .serializers import (
    SubmissionReviewSerializer,
    SubmissionReviewDetailSerializer,
    FieldSerializer,
    ReviewOpinionWriteSerializer
)
from .utils import get_review_form_fields_for_stage, review_workflow_actions

from ..stream_serializers import WagtailSerializer
from ..mixin import SubmissionNestedMixin
from ..permissions import IsApplyStaffUser


class SubmissionReviewViewSet(
    BaseStreamForm,
    WagtailSerializer,
    SubmissionNestedMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet
):
    permission_classes = (
        HasAPIKey | permissions.IsAuthenticated, HasAPIKey | IsApplyStaffUser,
    )
    serializer_class = SubmissionReviewSerializer

    def get_defined_fields(self):
        submission = self.get_submission_object()
        return get_review_form_fields_for_stage(submission)

    def get_object(self):
        return get_object_or_404(Review, id=self.kwargs['pk'])

    def get_queryset(self):
        submission = self.get_submission_object()
        self.queryset = self.model.objects.filter(submission=submission, is_draft=False)
        return super().get_queryset()

    def get_reviewer(self):
        submission = self.get_submission_object()
        ar, _ = AssignedReviewers.objects.get_or_create_for_user(
            submission=submission,
            reviewer=self.request.user,
        )
        return ar

    def create(self, request, *args, **kwargs):
        submission = self.get_submission_object()
        ser = self.get_serializer(data={
            '0069dea9-b6f3-46b5-9fdd-587a801fe803': 1,
            '9399a0e6-548c-4724-a35e-3c54709f0b33': 'comments',
            'e5d49655-34ba-4ecc-bc44-36836ee74c17': 'extra comments',
            '08a7f1d4-7527-4c22-8891-7bf3544768c2': 'rich text field'
        })
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
        ser = SubmissionReviewDetailSerializer(instance)
        return Response(ser.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        """Get details of a review on a submission"""
        review = self.get_object()
        ser = SubmissionReviewDetailSerializer(review)
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

        return Response(ser.data)

    def list(self, request, *args, **kwargs):
        """List all the reviews on a submission"""
        pass

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
        ser = ReviewOpinionWriteSerializer(data={'opinion': 1})
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
        return Response(status=status.HTTP_201_CREATED)
