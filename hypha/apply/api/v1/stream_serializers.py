import inspect
from collections import OrderedDict

from django.forms import TypedChoiceField
from rest_framework import serializers

from hypha.apply.review.fields import ScoredAnswerField
from hypha.apply.stream_forms.forms import BlockFieldWrapper

from .review.fields import ScoredAnswerListField

IGNORE_ARGS = ["self", "cls"]


class WagtailSerializer:
    def get_serializer_fields(self, draft=False):
        """
        Get the respective serializer fields for all the form fields.
        """
        serializer_fields = OrderedDict()
        form_fields = self.get_form_fields()
        for field_id, field in form_fields.items():
            serializer_fields[field_id] = self._get_field(
                field, self.get_serializer_field_class(field), draft
            )
        return serializer_fields

    def _get_field(self, form_field, serializer_field_class, draft=False):
        """
        Get the serializer field from the form field with all
        the kwargs defined.
        """
        kwargs = self._get_field_kwargs(form_field, serializer_field_class)
        field_kwargs = kwargs.copy()
        for kwarg, value in kwargs.items():
            # set corresponding DRF attributes which don't have alternative
            # in Django form fields
            if kwarg == "required":
                field_kwargs["allow_blank"] = not value
                field_kwargs["allow_null"] = not value

        if draft:
            # Set required false for fields if it's a draft.
            field_kwargs["required"] = False
            field_kwargs["allow_null"] = True
            field_kwargs["allow_blank"] = True
        try:
            field = serializer_field_class(**field_kwargs)
        except TypeError:
            # ScoredAnswerField doesn't have allow_blank attribute
            field_kwargs.pop("allow_blank")
            if serializer_field_class.__name__ == "ScoredAnswerListField":
                field_kwargs["draft"] = True
                return serializer_field_class(**field_kwargs)
            return serializer_field_class(**field_kwargs)

        return field

    def find_function_args(self, func):
        """
        Get the list of parameter names which function accepts.
        """
        try:
            spec = (
                inspect.getfullargspec(func)
                if hasattr(inspect, "getfullargspec")
                else inspect.getargspec(func)
            )
            return [i for i in spec[0] if i not in IGNORE_ARGS]
        except TypeError:
            return []

    def find_class_args(self, klass):
        """
        Find all class arguments (parameters) which can be passed in ``__init__``.
        """
        args = set()
        for i in klass.mro():
            if i is object or not hasattr(i, "__init__"):
                continue
            args |= set(self.find_function_args(i.__init__))

        return list(args)

    def find_matching_class_kwargs(self, reference_object, klass):
        return {
            i: getattr(reference_object, i)
            for i in self.find_class_args(klass)
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

        if "choices" in attrs:
            choices = OrderedDict(attrs["choices"]).keys()
            attrs["choices"] = OrderedDict(zip(choices, choices, strict=True))

        if getattr(form_field, "initial", None):
            attrs["default"] = form_field.initial

        # avoid "May not set both `required` and `default`"
        if attrs.get("required") and "default" in attrs:
            del attrs["required"]

        if isinstance(form_field, BlockFieldWrapper):
            attrs["read_only"] = True
            return attrs

        # avoid "May not set both `read_only` and `required`"
        if form_field.widget.attrs.get("readonly", False) == "readonly":
            attrs["read_only"] = True
            del attrs["required"]
        return attrs

    def get_serializer_field_class(self, field):
        """
        Assumes that a serializer field exist with the same name as form field.

        TODO:
        In case there are form fields not existing in serializer fields, we would
        have to create mapping b/w form fields and serializer fields to get the
        respective classes. But for now this works.
        """
        if isinstance(field, BlockFieldWrapper):
            return serializers.CharField
        if isinstance(field, ScoredAnswerField):
            return ScoredAnswerListField
        if isinstance(field, TypedChoiceField):
            return serializers.ChoiceField
        class_name = field.__class__.__name__
        return getattr(serializers, class_name)

    def get_serializer_class(self, draft=False):
        # Model serializers needs to have each field declared in the field options
        # of Meta. This code adds the dynamically generated serializer fields
        # to the serializer class meta fields.
        model_fields = [
            field
            for field in self.serializer_class.Meta.fields
            if hasattr(self.serializer_class.Meta.model, field)
        ]
        self.serializer_class.Meta.fields = model_fields + [
            *self.get_serializer_fields(draft).keys()
        ]
        return type(
            "WagtailStreamSerializer",
            (self.serializer_class,),
            self.get_serializer_fields(draft),
        )
