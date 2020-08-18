import inspect
import six
from collections import OrderedDict

from rest_framework import serializers

from hypha.apply.stream_forms.blocks import FormFieldBlock

IGNORE_ARGS = ['self', 'cls']


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
        self.serializer_class.Meta.fields = [*self.get_serializer_fields().keys()]
        return type('WagtailStreamSerializer', (self.serializer_class,), self.get_serializer_fields())
