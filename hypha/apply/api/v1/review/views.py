from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from wagtail.blocks.field_block import RichTextBlock

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
    HasReviewDetailPermission,
    HasReviewDraftPermission,
    HasReviewEditPermission,
    HasReviewOpinionPermission,
)
from .serializers import (
    FieldSerializer,
    ReviewOpinionWriteSerializer,
    SubmissionReviewSerializer,
)
from .utils import get_review_form_fields_for_stage, review_workflow_actions


class SubmissionReviewViewSet(
    BaseStreamForm, WagtailSerializer, SubmissionNestedMixin, viewsets.GenericViewSet
):
    permission_classes = (
        permissions.IsAuthenticated,
        IsApplyStaffUser,
    )
    permission_classes_by_action = {
        "create": [
            permissions.IsAuthenticated,
            HasReviewCreatePermission,
            IsApplyStaffUser,
        ],
        "retrieve": [
            permissions.IsAuthenticated,
            HasReviewDetailPermission,
            IsApplyStaffUser,
        ],
        "update": [
            permissions.IsAuthenticated,
            HasReviewEditPermission,
            IsApplyStaffUser,
        ],
        "delete": [
            permissions.IsAuthenticated,
            HasReviewDeletePermission,
            IsApplyStaffUser,
        ],
        "opinions": [
            permissions.IsAuthenticated,
            HasReviewOpinionPermission,
            IsApplyStaffUser,
        ],
        "fields": [
            permissions.IsAuthenticated,
            HasReviewCreatePermission,
            IsApplyStaffUser,
        ],
        "draft": [
            permissions.IsAuthenticated,
            HasReviewDraftPermission,
            IsApplyStaffUser,
        ],
    }
    serializer_class = SubmissionReviewSerializer

    def get_permissions(self):
        try:
            # return permission_classes depending on `action`
            return [
                permission()
                for permission in self.permission_classes_by_action[self.action]
            ]
        except KeyError:
            # action is not set return default permission_classes
            return [permission() for permission in self.permission_classes]

    def get_defined_fields(self):
        """
        Get form fields created for reviewing this submission.

        These form fields will be used to get respective serializer fields.
        """
        if self.action in ["retrieve", "update", "opinions"]:
            # For detail and edit api form fields used while submitting
            # review should be used.
            review = self.get_object()
            return review.form_fields
        if self.action == "draft":
            review = self.get_review_by_reviewer()
            return review.form_fields
        submission = self.get_submission_object()
        return get_review_form_fields_for_stage(submission)

    def get_serializer_class(self):
        """
        Override get_serializer_class to send draft parameter
        if the request is to save as draft or the review submitted
        is saved as draft.
        """
        if self.action == "retrieve":
            review = self.get_object()
            draft = review.is_draft
        elif self.action == "draft":
            draft = True
        else:
            draft = self.request.data.get("is_draft", False)
        return super().get_serializer_class(draft)

    def get_queryset(self):
        submission = self.get_submission_object()
        return Review.objects.filter(submission=submission, is_draft=False)

    def get_object(self):
        """
        Get the review object by id. If not found raise 404.
        """
        queryset = self.get_queryset()
        obj = get_object_or_404(queryset, id=self.kwargs["pk"])
        self.check_object_permissions(self.request, obj)
        return obj

    def get_reviewer(self):
        """
        Get the AssignedReviewers for the current user on a submission.
        """
        submission = self.get_submission_object()
        ar, _ = AssignedReviewers.objects.get_or_create_for_user(
            submission=submission,
            reviewer=self.request.user,
        )
        return ar

    def create(self, request, *args, **kwargs):
        """
        Create a review on a submission.

        Accept a post data in form of `{field_id: value}`.
        `field_id` is same id which you get from the `/fields` api.
        `value` should be submitted with html tags, so that response can
        be displayed with correct formatting, e.g. in case of rich text field,
        we need to show the data with same formatting user has submitted.

        Accepts optional parameter `is_draft` when a review is to be saved as draft.

        Raise ValidationError if a review is already submitted by the user.
        """
        submission = self.get_submission_object()
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        instance, create = ser.Meta.model.objects.get_or_create(
            submission=submission, author=self.get_reviewer()
        )
        if not create and not instance.is_draft:
            raise ValidationError(
                {"detail": "You have already posted a review for this submission"}
            )
        instance.form_fields = self.get_defined_fields()
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
        ser = self.get_serializer(self.get_review_data(instance))
        return Response(ser.data, status=status.HTTP_201_CREATED)

    def get_review_data(self, review):
        """
        Get review data which will be used for review detail api.
        """
        review_data = review.form_data
        review_data["id"] = review.id
        review_data["score"] = review.score
        review_data["opinions"] = review.opinions
        review_data["is_draft"] = review.is_draft
        for field_block in review.form_fields:
            if isinstance(field_block.block, RichTextBlock):
                review_data[field_block.id] = field_block.value.source
        return review_data

    def retrieve(self, request, *args, **kwargs):
        """
        Get details of a review on a submission
        """
        review = self.get_object()
        ser = self.get_serializer(self.get_review_data(review))
        return Response(ser.data)

    def update(self, request, *args, **kwargs):
        """
        Update a review submitted on a submission.
        """
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
        ser = self.get_serializer(self.get_review_data(review))
        return Response(ser.data)

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

    def get_review_by_reviewer(self):
        submission = self.get_submission_object()
        review = Review.objects.get(
            submission=submission, author__reviewer=self.request.user
        )
        return review

    @action(detail=False, methods=["get"])
    def draft(self, request, *args, **kwargs):
        """
        Returns the draft review submitted on a submission by current user.
        """
        try:
            review = self.get_review_by_reviewer()
        except Review.DoesNotExist:
            return Response({})
        if not review.is_draft:
            return Response({})
        ser = self.get_serializer(self.get_review_data(review))
        return Response(ser.data)

    @action(detail=False, methods=["get"])
    def fields(self, request, *args, **kwargs):
        """
        List details of all the form fields that were created by admin for adding reviews.

        These field details will be used in frontend to render the review form.
        """
        fields = self.get_form_fields()
        fields = FieldSerializer(fields.items(), many=True)
        return Response(fields.data)

    @action(detail=True, methods=["post"])
    def opinions(self, request, *args, **kwargs):
        """
        Used to add opinions on a review.

        Options are 0 and 1. DISAGREE = 0 AGREE = 1

        Response is similar to detail api of the review.
        """
        review = self.get_object()
        ser = ReviewOpinionWriteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        opinion = ser.validated_data["opinion"]
        try:
            review_opinion = ReviewOpinion.objects.get(
                review=review, author=self.get_reviewer()
            )
        except ReviewOpinion.DoesNotExist:
            ReviewOpinion.objects.create(
                review=review, author=self.get_reviewer(), opinion=opinion
            )
        else:
            review_opinion.opinion = opinion
            review_opinion.save()
        ser = self.get_serializer(self.get_review_data(review))
        return Response(ser.data, status=status.HTTP_201_CREATED)
