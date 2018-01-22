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


class MustIncludeStatic(StaticBlock):
    def __init__(self, *args, description='', **kwargs):
        self.description = description
        super().__init__(*args, **kwargs)

    class Meta:
        admin_text = 'Much be included in the form once.'

    def render_form(self, *args, **kwargs):
        form = super().render_form(*args, **kwargs)
        form = '<br>'.join([self.description, form])
        return mark_safe(form)


class MustIncludeFieldBlock(FormFieldBlock):
    def __init__(self, *args, **kwargs):
        info_name = f'{self.name}_field'
        child_blocks = [(info_name, MustIncludeStatic(description=self.description))]
        super().__init__(child_blocks, *args, **kwargs)


class TitleBlock(MustIncludeFieldBlock):
    name = 'title'
    description = 'The title of the project'


class ValueBlock(MustIncludeFieldBlock):
    name = 'value'
    description = 'The value of the project'
