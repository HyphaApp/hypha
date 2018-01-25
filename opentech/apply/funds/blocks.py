from collections import Counter

from django import forms
from django.core.exceptions import ValidationError
from django.forms.utils import ErrorList
from django.utils.translation import ugettext_lazy as _
from django.utils.text import mark_safe

from wagtail.wagtailcore.blocks import StaticBlock

from tinymce.widgets import TinyMCE

from opentech.apply.stream_forms.blocks import FormFieldsBlock, FormFieldBlock, TextFieldBlock
from opentech.apply.categories.blocks import CategoryQuestionBlock


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
    widget = TinyMCE(mce_attrs={
        'elementpath': False,
        'branding': False,
    })

    class Meta:
        label = _('Rich text field')
        icon = 'form'


class CustomFormFieldsBlock(FormFieldsBlock):
    rich_text = RichTextFieldBlock(group=_('Fields'))
    category = CategoryQuestionBlock(group=_('Custom'))

    def __init__(self, *args, **kwargs):
        child_blocks = [(block.name, block(group=_('Required'))) for block in MustIncludeFieldBlock.__subclasses__()]
        super().__init__(child_blocks, *args, **kwargs)

    def clean(self, value):
        try:
            value = super().clean(value)
        except ValidationError as e:
            error_dict = e.params
        else:
            error_dict = dict()

        block_types = [block.block_type for block in value]
        missing = set(REQUIRED_BLOCK_NAMES) - set(block_types)

        duplicates = [
            name for name in find_duplicates(block_types)
            if name in REQUIRED_BLOCK_NAMES
        ]

        all_errors = list()
        if missing:
            all_errors.append(
                'You are missing the following required fields: {}'.format(', '.join(prettify_names(missing)))
            )

        if duplicates:
            all_errors.append(
                'You have duplicates of the following required fields: {}'.format(', '.join(prettify_names(duplicates)))
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


class MustIncludeStatic(StaticBlock):
    """Helper block which displays additional information about the must include block and
    helps display the error in a noticeable way.
    """
    def __init__(self, *args, description='', **kwargs):
        self.description = description
        super().__init__(*args, **kwargs)

    class Meta:
        admin_text = 'Much be included in the form only once.'

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
        return ('wagtail.wagtailcore.blocks.static_block.StaticBlock', (), {})


class MustIncludeFieldBlock(FormFieldBlock):
    """Any block inheriting from this will need to be included in the application forms
    This data will also be available to query on the submission object
    """
    def __init__(self, *args, **kwargs):
        info_name = f'{self.name.title()} Field'
        child_blocks = [('info', MustIncludeStatic(label=info_name, description=self.description))]
        super().__init__(child_blocks, *args, **kwargs)

    def get_field_kwargs(self, struct_value):
        kwargs = super().get_field_kwargs(struct_value)
        kwargs['required'] = True
        return kwargs


class TitleBlock(MustIncludeFieldBlock):
    name = 'title'
    description = 'The title of the project'


class ValueBlock(MustIncludeFieldBlock):
    name = 'value'
    description = 'The value of the project'
    widget = forms.NumberInput


class EmailBlock(MustIncludeFieldBlock):
    name = 'email'
    description = 'The applicant email address'
    widget = forms.EmailInput

    class Meta:
        icon = 'user'


class FullNameBlock(MustIncludeFieldBlock):
    name = 'full_name'
    description = 'Full name'

    class Meta:
        icon = 'mail'

REQUIRED_BLOCK_NAMES = [block.name for block in MustIncludeFieldBlock.__subclasses__()]
