from collections import OrderedDict

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.db import transaction
from django.db.models import Prefetch
from django.utils import timezone
from django_filters import rest_framework as filters
from rest_framework import mixins, permissions, viewsets, serializers
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey
import inspect, six
from hypha.apply.activity.messaging import MESSAGES, messenger
from hypha.apply.activity.models import COMMENT, Activity
from hypha.apply.determinations.views import DeterminationCreateOrUpdateView
from hypha.apply.funds.models import ApplicationSubmission, RoundsAndLabs
from hypha.apply.review.models import Review

from .filters import CommentFilter, SubmissionsFilter
from .mixin import SubmissionNextedMixin
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


class WagtailSerializer:
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
        return type('WagtailStreamSerializer', (self.serializer_class,), self.get_serializer_fields())


class SubmissionReviewSerializer(serializers.ModelSerializer, metaclass=serializers.SerializerMetaclass):
    justtopost = serializers.CharField()

    class Meta:
        model = Review
        fields = ['recommendation', 'visibility', 'score', 'submission']

    def validate(self):
        import ipdb; ipdb.set_trace()
        validated_data = super().validate()
        validated_data['form_data'] = {
            key: value
            for key, value in validated_data.items()
            if key not in self._meta.fields
        }
        return validated_data

    def save(self):
        import ipdb; ipdb.set_trace()
        pass


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


class SubmissionReviewViewSet(
    WagtailSerializer,
    SubmissionNextedMixin,
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

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data={'0069dea9-b6f3-46b5-9fdd-587a801fe803': 5})
        ser.is_valid(raise_exception=True)
        return Response({})

    @action(detail=False, methods=['get'])
    def fields(self, request, *args, **kwargs):
        submission = self.get_submission_object()
        fields = get_review_form_fields_for_stage(submission)
        ser = FieldSerializer(fields, many=True)
        return Response(ser.data)
