from django import forms
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from wagtail.blocks.field_block import RichTextBlock

from hypha.apply.activity.messaging import MESSAGES, messenger
from hypha.apply.activity.models import Activity
from hypha.apply.determinations.blocks import DeterminationBlock
from hypha.apply.determinations.models import Determination
from hypha.apply.determinations.options import NEEDS_MORE_INFO
from hypha.apply.determinations.utils import (
    has_final_determination,
    transition_from_outcome,
)
from hypha.apply.projects.models import Project
from hypha.apply.stream_forms.models import BaseStreamForm

from ..mixin import SubmissionNestedMixin
from ..permissions import IsApplyStaffUser
from ..review.serializers import FieldSerializer
from ..stream_serializers import WagtailSerializer
from .permissions import (
    HasDeterminationCreatePermission,
    HasDeterminationDraftPermission,
)
from .serializers import SubmissionDeterminationSerializer
from .utils import get_fields_for_stage, outcome_choices_for_phase


class SubmissionDeterminationViewSet(
    BaseStreamForm, WagtailSerializer, SubmissionNestedMixin, viewsets.GenericViewSet
):
    permission_classes = (
        permissions.IsAuthenticated,
        IsApplyStaffUser,
    )
    permission_classes_by_action = {
        "create": [
            permissions.IsAuthenticated,
            HasDeterminationCreatePermission,
            IsApplyStaffUser,
        ],
        "draft": [
            permissions.IsAuthenticated,
            HasDeterminationDraftPermission,
            IsApplyStaffUser,
        ],
    }
    serializer_class = SubmissionDeterminationSerializer

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
        Get form fields created for determining this submission.

        These form fields will be used to get respective serializer fields.
        """
        if self.action in ["retrieve", "update"]:
            # For detail and edit api form fields used while submitting
            # determination should be used.
            determination = self.get_object()
            return determination.form_fields
        submission = self.get_submission_object()
        return get_fields_for_stage(submission)

    def get_serializer_class(self):
        """
        Override get_serializer_class to send draft parameter
        if the request is to save as draft or the determination submitted
        is saved as draft.
        """
        if self.action == "retrieve":
            determination = self.get_object()
            draft = determination.is_draft
        elif self.action == "draft":
            draft = True
        else:
            draft = self.request.data.get("is_draft", False)
        return super().get_serializer_class(draft)

    def get_queryset(self):
        submission = self.get_submission_object()
        return Determination.objects.filter(submission=submission, is_draft=False)

    def get_object(self):
        """
        Get the determination object by id. If not found raise 404.
        """
        queryset = self.get_queryset()
        obj = get_object_or_404(queryset, id=self.kwargs["pk"])
        self.check_object_permissions(self.request, obj)
        return obj

    def get_determination_data(self, determination):
        """
        Get determination data which will be used for determination detail api.
        """
        determination_data = determination.form_data
        field_blocks = determination.form_fields
        for field_block in field_blocks:
            if isinstance(field_block.block, DeterminationBlock):
                determination_data[field_block.id] = determination.outcome
            if isinstance(field_block.block, RichTextBlock):
                determination_data[field_block.id] = field_block.value.source
        determination_data["id"] = determination.id
        determination_data["is_draft"] = determination.is_draft
        return determination_data

    def retrieve(self, request, *args, **kwargs):
        """
        Get details of a determination on a submission
        """
        determination = self.get_object()
        ser = self.get_serializer(self.get_determination_data(determination))
        return Response(ser.data)

    def get_form_fields(self):
        form_fields = super(SubmissionDeterminationViewSet, self).get_form_fields()
        submission = self.get_submission_object()
        field_blocks = self.get_defined_fields()
        for field_block in field_blocks:
            if isinstance(field_block.block, DeterminationBlock):
                outcome_choices = outcome_choices_for_phase(
                    submission, self.request.user
                )
                if self.action == "update":
                    # Outcome can not be edited after being set once, so we do not
                    # need to render this field.
                    # form_fields.pop(field_block.id)
                    form_fields[field_block.id].widget = forms.TextInput(
                        attrs={"readonly": "readonly"}
                    )
                else:
                    # Outcome field choices need to be set according to the phase.
                    form_fields[field_block.id].choices = outcome_choices
        return form_fields

    @action(detail=False, methods=["get"])
    def fields(self, request, *args, **kwargs):
        """
        List details of all the form fields that were created by admin for adding determinations.

        These field details will be used in frontend to render the determination form.
        """
        form_fields = self.get_form_fields()
        fields = FieldSerializer(form_fields.items(), many=True)
        return Response(fields.data)

    def get_draft_determination(self):
        submission = self.get_submission_object()
        try:
            determination = Determination.objects.get(
                submission=submission, is_draft=True
            )
        except Determination.DoesNotExist:
            return
        else:
            return determination

    @action(detail=False, methods=["get"])
    def draft(self, request, *args, **kwargs):
        """
        Returns the draft determination submitted on a submission by current user.
        """
        determination = self.get_draft_determination()
        if not determination:
            return Response({})
        ser = self.get_serializer(self.get_determination_data(determination))
        return Response(ser.data)

    def create(self, request, *args, **kwargs):
        """
        Create a determination on a submission.

        Accept a post data in form of `{field_id: value}`.
        `field_id` is same id which you get from the `/fields` api.
        `value` should be submitted with html tags, so that response can
        be displayed with correct formatting, e.g. in case of rich text field,
        we need to show the data with same formatting user has submitted.

        Accepts optional parameter `is_draft` when a determination is to be saved as draft.

        Raise ValidationError if a determination is already submitted by the user.
        """
        submission = self.get_submission_object()
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        if has_final_determination(submission):
            return ValidationError(
                {"detail": "A final determination has already been submitted."}
            )
        determination = self.get_draft_determination()
        if determination is None:
            determination = Determination.objects.create(
                submission=submission, author=request.user
            )
        determination.form_fields = self.get_defined_fields()
        determination.save()
        ser.update(determination, ser.validated_data)
        if determination.is_draft:
            ser = self.get_serializer(self.get_determination_data(determination))
            return Response(ser.data, status=status.HTTP_201_CREATED)
        with transaction.atomic():
            messenger(
                MESSAGES.DETERMINATION_OUTCOME,
                request=self.request,
                user=determination.author,
                submission=submission,
                related=determination,
            )
            proposal_form = ser.validated_data.get("proposal_form")
            transition = transition_from_outcome(int(determination.outcome), submission)

            if determination.outcome == NEEDS_MORE_INFO:
                # We keep a record of the message sent to the user in the comment
                Activity.comments.create(
                    message=determination.stripped_message,
                    timestamp=timezone.now(),
                    user=self.request.user,
                    source=submission,
                    related_object=determination,
                )
            submission.perform_transition(
                transition,
                self.request.user,
                request=self.request,
                notify=False,
                proposal_form=proposal_form,
            )

            if submission.accepted_for_funding and settings.PROJECTS_AUTO_CREATE:
                Project.create_from_submission(submission)

        messenger(
            MESSAGES.DETERMINATION_OUTCOME,
            request=self.request,
            user=determination.author,
            source=submission,
            related=determination,
        )
        ser = self.get_serializer(self.get_determination_data(determination))
        return Response(ser.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """
        Update a determination submitted on a submission.
        """
        determination = self.get_object()
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.update(determination, ser.validated_data)

        messenger(
            MESSAGES.DETERMINATION_OUTCOME,
            request=self.request,
            user=determination.author,
            source=determination.submission,
            related=determination,
        )
        ser = self.get_serializer(self.get_determination_data(determination))
        return Response(ser.data)
