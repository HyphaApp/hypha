from collections import Counter

from django.core.exceptions import ValidationError
from django.forms.utils import ErrorList
from django.utils.translation import ugettext_lazy as _
from django.utils.text import mark_safe

from wagtail.wagtailcore.blocks import StaticBlock
from opentech.apply.stream_forms.blocks import FormFieldsBlock, FormFieldBlock

from opentech.apply.categories.blocks import CategoryQuestionBlock


class CustomFormFieldsBlock(FormFieldsBlock):
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

        counted_types = Counter(block_types)
        duplicates = [
            name for name, count in counted_types.items()
            if name in REQUIRED_BLOCK_NAMES and count > 1
        ]

        all_errors = list()
        if missing:
            all_errors.append(
                'You are missing the following required fields: {}'.format(', '.join(missing).title())
            )

        if duplicates:
            all_errors.append(
                'You have duplicates of the following required fields: {}'.format(', '.join(duplicates).title())
            )
            for name in duplicates:
                for i, block_name in enumerate(block_types):
                    if block_name == name:
                        try:
                            error_dict[i].data[0].params['info'] = ErrorList(['Duplicate'])
                        except KeyError:
                            error_dict[i] = ErrorList(
                                [ValidationError('Error', params={'info': ErrorList(['Duplicate'])})]
                            )

        if all_errors:
            error_dict['__all__'] = all_errors
            raise ValidationError('Error', params=error_dict)

        return value


class MustIncludeStatic(StaticBlock):
    def __init__(self, *args, description='', **kwargs):
        self.description = description
        super().__init__(*args, **kwargs)

    class Meta:
        admin_text = 'Much be included in the form once.'

    def render_form(self, *args, **kwargs):
        errors = kwargs.pop('errors')
        if errors:
            # Pretend the error is a readonly input so that we get nice formatting
            error_message= '<div class="error"><input readonly placeholder="{}"></div>'.format(errors[0])
        else:
            error_message = ''
        form = super().render_form(*args, **kwargs)
        form = '<br>'.join([self.description, form]) + error_message
        return mark_safe(form)


class MustIncludeFieldBlock(FormFieldBlock):
    def __init__(self, *args, **kwargs):
        info_name = f'{self.name.title()} Field'
        child_blocks = [('info', MustIncludeStatic(label=info_name, description=self.description))]
        super().__init__(child_blocks, *args, **kwargs)


class TitleBlock(MustIncludeFieldBlock):
    name = 'title'
    description = 'The title of the project'


class ValueBlock(MustIncludeFieldBlock):
    name = 'value'
    description = 'The value of the project'


REQUIRED_BLOCK_NAMES = [block.name  for block in MustIncludeFieldBlock.__subclasses__()]
