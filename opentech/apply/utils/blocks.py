from collections import Counter

import bleach
from django.core.exceptions import ValidationError
from django.forms.utils import ErrorList
from django.utils.translation import ugettext_lazy as _
from django.utils.text import mark_safe

from wagtail.core.blocks import StaticBlock, StreamValue, StreamBlock

from opentech.apply.stream_forms.blocks import FormFieldBlock, OptionalFormFieldBlock, TextFieldBlock
from opentech.apply.utils.options import RICH_TEXT_WIDGET


def find_duplicates(items):
    counted = Counter(items)
    duplicates = [
        name for name, count in counted.items() if count > 1
    ]
    return duplicates


def prettify_names(sequence):
    return [nice_field_name(item) for item in sequence]


def nice_field_name(name):
    return name.title().replace('_', ' ')


class RichTextFieldBlock(TextFieldBlock):
    widget = RICH_TEXT_WIDGET

    class Meta:
        label = _('Rich text field')
        icon = 'form'

    def get_searchable_content(self, value, data):
        return bleach.clean(data or '', tags=[], strip=True)

    def no_response(self):
        return '<p>No response</p>'


class CustomFormFieldsBlock(StreamBlock):
    rich_text = RichTextFieldBlock(group=_('Fields'))
    required_blocks = []
    single_blocks = []

    def __init__(self, *args, **kwargs):
        child_blocks = [(block.name, block(group=_(' Required'))) for block in self.required_blocks]
        child_blocks += [(block.name, block(group=_('Custom'))) for block in self.single_blocks]
        self.required_block_names = [block.name for block in self.required_blocks]
        self.single_block_names = [block.name for block in self.single_blocks] + self.required_block_names

        super().__init__(child_blocks, *args, **kwargs)

    def clean(self, value):
        try:
            value = super().clean(value)
        except ValidationError as e:
            error_dict = e.params
        else:
            error_dict = dict()

        block_types = [block.block_type for block in value]
        missing = set(self.required_block_names) - set(block_types)

        duplicates = [
            name for name in find_duplicates(block_types)
            if name in self.single_block_names
        ]

        all_errors = list()
        if missing:
            all_errors.append(
                'You are missing the following required fields: {}'.format(', '.join(prettify_names(missing)))
            )

        if duplicates:
            all_errors.append(
                'The following fields must be included only once: {}'.format(', '.join(prettify_names(duplicates)))
            )
            for i, block_name in enumerate(block_types):
                if block_name in duplicates:
                    self.add_error_to_child(error_dict, i, 'info', 'Duplicate field')

        if all_errors or error_dict:
            error_dict['__all__'] = all_errors
            raise ValidationError('Error', params=error_dict)

        return value

    def add_error_to_child(self, errors, child_number, field, message):
        new_error = ErrorList([message])
        try:
            errors[child_number].data[0].params[field] = new_error
        except KeyError:
            errors[child_number] = ErrorList(
                [ValidationError('Error', params={field: new_error})]
            )

    def to_python(self, value):
        """
        This allows historic data to still be accessible even
        if a custom field type is removed from the code in the future.
        """
        # If the data type is missing, fallback to a CharField
        for child_data in value:
            if child_data['type'] not in self.child_blocks:
                child_data['type'] = 'char'

        return StreamValue(self, value, is_lazy=True)


class SingleIncludeStatic(StaticBlock):
    """Helper block which displays additional information about the must include block and
    helps display the error in a noticeable way.
    """

    def __init__(self, *args, description='', **kwargs):
        self.description = description
        super().__init__(*args, **kwargs)

    class Meta:
        admin_text = 'Must be included in the form only once.'

    def render_form(self, *args, **kwargs):
        errors = kwargs.pop('errors')
        if errors:
            # Pretend the error is a readonly input so that we get nice formatting
            # Issue discussed here: https://github.com/wagtail/wagtail/issues/4122
            error_message = '<div class="error"><input readonly placeholder="{}"></div>'.format(errors[0])
        else:
            error_message = ''
        form = super().render_form(*args, **kwargs)
        form = '<br>'.join([self.description, form]) + error_message
        return mark_safe(form)

    def deconstruct(self):
        return ('wagtail.core.blocks.static_block.StaticBlock', (), {})


class SingleIncludeMixin:
    def __init__(self, *args, **kwargs):
        info_name = f'{self.name.title()} Field'
        child_blocks = [('info', SingleIncludeStatic(label=info_name, description=self.description))]
        super().__init__(child_blocks, *args, **kwargs)


class SingleIncludeBlock(SingleIncludeMixin, OptionalFormFieldBlock):
    """A block that is only allowed to be included once in the form, but is optional"""


class MustIncludeFieldBlock(SingleIncludeMixin, FormFieldBlock):
    """Any block inheriting from this will need to be included in the application forms
    This data will also be available to query on the submission object
    """

    def get_field_kwargs(self, struct_value):
        kwargs = super().get_field_kwargs(struct_value)
        kwargs['required'] = True
        return kwargs
