from collections import OrderedDict

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.db import transaction
from django.db.models import Prefetch
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from rest_framework import mixins, permissions, viewsets, serializers, status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey
import inspect, six
from hypha.apply.activity.messaging import MESSAGES, messenger
from hypha.apply.activity.models import COMMENT, Activity
from hypha.apply.determinations.views import DeterminationCreateOrUpdateView
from hypha.apply.funds.models import ApplicationSubmission, RoundsAndLabs, AssignedReviewers
from hypha.apply.review.models import Review, ReviewOpinion
from hypha.apply.review.options import PRIVATE, NA, OPINION_CHOICES
from hypha.apply.funds.workflow import INITIAL_STATE

from .filters import CommentFilter, SubmissionsFilter
from .mixin import SubmissionNestedMixin, ReviewNestedMixin
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
from .utils import get_review_form_fields_for_stage
from hypha.apply.stream_forms.blocks import FormFieldBlock

IGNORE_ARGS = ['self', 'cls']


class MixedFieldMetaclass(serializers.SerializerMetaclass):
    """Stores all fields passed to the class and not just the field type.
    This allows the form to be rendered when Field-like blocks are passed
    in as part of the definition
    """
    def __new__(mcs, name, bases, attrs):
        display = attrs.copy()
        new_class = super(MixedFieldMetaclass, mcs).__new__(mcs, name, bases, attrs)
        new_class.display = display
        return new_class


class StreamBaseSerializer(serializers.Serializer, metaclass=MixedFieldMetaclass):
    def swap_fields_for_display(func):
        def wrapped(self, *args, **kwargs):
            # Replaces the form fields with the display fields
            # should only add new streamblocks and wont affect validation
            import ipdb; ipdb.set_trace()
            fields = self.fields.copy()
            self.fields = self.display
            yield from func(self, *args, **kwargs)
            self.fields = fields
        return wrapped

    @swap_fields_for_display
    def __iter__(self):
        import ipdb; ipdb.set_trace()
        yield from super().__iter__()


class PageStreamBaseSerializer(StreamBaseSerializer):
    # Adds page and user reference to the form class
    pass


class WagtailSerializer:
    # submission_serializer_class = PageStreamBaseSerializer

    def get_serializer_fields(self):
        serializer_fields = OrderedDict()
        field_blocks = self.get_defined_fields()
        for struct_child in field_blocks:
            block = struct_child.block
            struct_value = struct_child.value
            if isinstance(block, FormFieldBlock):
                field_class = block.field_class.__name__
                field_from_block = block.get_field(struct_value)
                serializer_fields[struct_child.id] = self._get_field(
                    field_from_block,
                    self.get_serializer_field_class(field_class)
                )
        return serializer_fields

    def _get_field(self, form_field, serializer_field_class):
        import ipdb; ipdb.set_trace()
        kwargs = self._get_field_kwargs(form_field, serializer_field_class)

        field = serializer_field_class(**kwargs)

        for kwarg, value in kwargs.items():
            # set corresponding DRF attributes which don't have alternative
            # in Django form fields
            if kwarg == 'required':
                field.allow_blank = not value
                field.allow_null = not value

            # ChoiceField natively uses choice_strings_to_values
            # in the to_internal_value flow
            elif kwarg == 'choices':
                field.choice_strings_to_values = {
                    six.text_type(key): key for key in OrderedDict(value).keys()
                }

        return field

    def find_function_args(self, func):
        """
        Get the list of parameter names which function accepts.
        """
        try:
            spec = inspect.getfullargspec(func) if hasattr(inspect, 'getfullargspec') else inspect.getargspec(func)
            return [i for i in spec[0] if i not in IGNORE_ARGS]
        except TypeError:
            return []

    def find_class_args(self, klass):
        """
        Find all class arguments (parameters) which can be passed in ``__init__``.
        """
        args = set()

        for i in klass.mro():
            if i is object or not hasattr(i, '__init__'):
                continue
            args |= set(self.find_function_args(i.__init__))

        return list(args)

    def find_matching_class_kwargs(self, reference_object, klass):
        return {
            i: getattr(reference_object, i) for i in self.find_class_args(klass)
            if hasattr(reference_object, i)
        }

    def _get_field_kwargs(self, form_field, serializer_field_class):
        """
        For a given Form field, determine what validation attributes
        have been set.  Includes things like max_length, required, etc.
        These will be used to create an instance of ``rest_framework.fields.Field``.
        :param form_field: a ``django.forms.field.Field`` instance
        :return: dictionary of attributes to set
        """
        attrs = self.find_matching_class_kwargs(form_field, serializer_field_class)

        if 'choices' in attrs:
            choices = OrderedDict(attrs['choices']).keys()
            attrs['choices'] = OrderedDict(zip(choices, choices))

        if getattr(form_field, 'initial', None):
            attrs['default'] = form_field.initial

        # avoid "May not set both `required` and `default`"
        if attrs.get('required') and 'default' in attrs:
            del attrs['required']

        return attrs

    def get_defined_fields(self):
        return self.form_fields

    def get_serializer_field_class(self, field_class):
        return getattr(serializers, field_class)

    def get_serializer_class(self):
        import ipdb; ipdb.set_trace()
        self.serializer_class.Meta.fields = [*self.get_serializer_fields().keys()]
        return type('WagtailStreamSerializer', (self.serializer_class,), self.get_serializer_fields())


class MixedMetaClass(type(StreamBaseSerializer), type(serializers.ModelSerializer)):
    pass


class OpinionSerializer(serializers.ModelSerializer):
    author_id = serializers.ReadOnlyField(source='author.id')
    opinion = serializers.ReadOnlyField(source='get_opinion_display')

    class Meta:
        model = ReviewOpinion
        fields = ('author_id', 'opinion')


class SubmissionReviewSerializer2(serializers.ModelSerializer):
    author_id = serializers.ReadOnlyField(source='author.id')
    # url = serializers.ReadOnlyField(source='get_absolute_url')
    opinions = OpinionSerializer(read_only=True, many=True)
    recommendation = serializers.SerializerMethodField()
    score = serializers.ReadOnlyField(source='get_score_display')

    class Meta:
        model = Review
        fields = ['id', 'score', 'author_id', 'opinions', 'recommendation', 'form_data']

    def get_recommendation(self, obj):
        return {
            'value': obj.recommendation,
            'display': obj.get_recommendation_display(),
        }


class SubmissionReviewSerializer(serializers.ModelSerializer, metaclass=serializers.SerializerMetaclass):

    class Meta:
        model = Review
        fields = []

    def get_recommendation(self, obj):
        return {
            'value': obj.recommendation,
            'display': obj.get_recommendation_display(),
        }

    def validate(self, data):
        validated_data = super().validate(data)
        validated_data['form_data'] = {
            key: value
            for key, value in validated_data.items()
        }
        return validated_data

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        instance.score = self.calculate_score(instance, self.validated_data)
        instance.recommendation = int(self.validated_data[instance.recommendation_field.id])
        try:
            instance.visibility = self.validated_data[instance.visibility_field.id]
        except AttributeError:
            instance.visibility = PRIVATE

        if not instance.is_draft:
            # Capture the revision against which the user was reviewing
            instance.revision = instance.submission.live_revision

        instance.save()
        return instance

    def calculate_score(self, instance, data):
        scores = list()
        for field in instance.score_fields:
            score = data.get(field.id)[1]
            # Include NA answers as 0.
            if score == NA:
                score = 0
            scores.append(score)
        # Check if there are score_fields_without_text and also
        # append scores from them.
        for field in instance.score_fields_without_text:
            score = data.get(field.id)
            # Include '' answers as 0.
            if score == '':
                score = 0
            scores.append(int(score))

        try:
            return sum(scores) / len(scores)
        except ZeroDivisionError:
            return NA


class FieldSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    kwargs = serializers.SerializerMethodField()

    def get_id(self, obj):
        return obj.id

    def get_type(self, obj):
        return obj.block.field_class.__name__

    def get_kwargs(self, obj):
        struct_value = obj.value
        kwargs = obj.block.get_field_kwargs(struct_value)
        kwargs.pop('widget', False)
        return kwargs


def review_workflow_actions(request, submission):
    submission_stepped_phases = submission.workflow.stepped_phases
    action = None
    if submission.status == INITIAL_STATE:
        # Automatically transition the application to "Internal review".
        action = submission_stepped_phases[2][0].name
    elif submission.status == 'proposal_discussion':
        # Automatically transition the proposal to "Internal review".
        action = 'proposal_internal_review'
    elif submission.status == submission_stepped_phases[2][0].name and submission.reviews.count() > 1:
        # Automatically transition the application to "Ready for discussion".
        action = submission_stepped_phases[3][0].name
    elif submission.status == 'ext_external_review' and submission.reviews.by_reviewers().count() > 1:
        # Automatically transition the application to "Ready for discussion".
        action = 'ext_post_external_review_discussion'
    elif submission.status == 'com_external_review' and submission.reviews.by_reviewers().count() > 1:
        # Automatically transition the application to "Ready for discussion".
        action = 'com_post_external_review_discussion'
    elif submission.status == 'external_review' and submission.reviews.by_reviewers().count() > 1:
        # Automatically transition the proposal to "Ready for discussion".
        action = 'post_external_review_discussion'

    # If action is set run perform_transition().
    if action:
        try:
            submission.perform_transition(
                action,
                request.user,
                request=request,
                notify=False,
            )
        except (PermissionDenied, KeyError):
            pass


# class ReviewOpinionSerializer(serializers.Serializer):
#     author = serializers.ReviewOpinion
#     class Meta:
#         model = ReviewOpinion
#         fields = ('author', 'opinion',)


class SubmissionReviewViewSet(
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

    def create(self, request, *args, **kwargs):
        submission = self.get_submission_object()
        ser = self.get_serializer(data={
            '0069dea9-b6f3-46b5-9fdd-587a801fe803': 1,
            'justtopost': 'justpostsomething'
        })
        ser.is_valid(raise_exception=True)
        ar, _ = AssignedReviewers.objects.get_or_create_for_user(
            submission=submission,
            reviewer=request.user,
        )
        instance = ser.Meta.model.objects.create(
            form_fields=self.get_defined_fields(),
            submission=submission, author=ar
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

        return Response(ser.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        """Get details of a review on a submission"""
        review = self.get_object()
        ser = SubmissionReviewSerializer2(review)
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
        submission = self.get_submission_object()
        fields = get_review_form_fields_for_stage(submission)
        ser = FieldSerializer(fields, many=True)
        return Response(ser.data)


class ReviewOpinionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewOpinion
        fields = ('author', 'opinion',)

    def validate(self):
        validated_data = super().validate()
        import ipdb; ipdb.set_trace()
        return validated_data


class ReviewOptionSerializer(serializers.Serializer):
    options = serializers.DictField()


class ReviewOpinionViewSet(
    SubmissionNestedMixin,
    ReviewNestedMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    permission_classes = (
        HasAPIKey | permissions.IsAuthenticated, HasAPIKey | IsApplyStaffUser,
    )
    serializer_class = ReviewOpinionSerializer

    def get_queryset(self):
        review = self.get_review_object()
        return review.opinions.all()

    def create(self, request, *args, **kwargs):
        pass

    # def list(self, request, *args, **kwargs):
    #     pass

    # def update(self, request, *args, **kwargs):
    #     instance=review.opinions.filter(author__reviewer=self.request.user).first()
    #     pass

    @action(detail=False, methods=['get'])
    def options(self, request, *args, **kwargs):
        return Response(dict(OPINION_CHOICES))
