from django import forms
from django.utils.translation import gettext_lazy as _
from wagtail.blocks import RichTextBlock

from hypha.apply.stream_forms.blocks import (
    CharFieldBlock,
    CheckboxFieldBlock,
    DropdownFieldBlock,
    TextFieldBlock,
)
from hypha.apply.utils.blocks import CustomFormFieldsBlock, MustIncludeFieldBlock
from hypha.apply.utils.options import RICH_TEXT_WIDGET

from .options import DETERMINATION_CHOICES


class DeterminationMustIncludeFieldBlock(MustIncludeFieldBlock):
    pass


class DeterminationBlock(DeterminationMustIncludeFieldBlock):
    name = 'determination'
    description = 'Overall determination'
    field_class = forms.TypedChoiceField

    class Meta:
        icon = 'pick'

    def get_field_kwargs(self, struct_value):
        kwargs = super().get_field_kwargs(struct_value)
        kwargs['choices'] = DETERMINATION_CHOICES
        return kwargs

    def render(self, value, context=None):
        data = int(context['data'])
        choices = dict(DETERMINATION_CHOICES)
        context['data'] = choices[data]
        return super().render(value, context)


class DeterminationMessageBlock(DeterminationMustIncludeFieldBlock):
    name = 'message'
    description = 'Determination message'
    widget = RICH_TEXT_WIDGET

    class Meta:
        icon = 'openquote'
        template = 'stream_forms/render_unsafe_field.html'

    def get_field_kwargs(self, struct_value):
        kwargs = super().get_field_kwargs(struct_value)
        kwargs['required'] = False
        return kwargs


class SendNoticeBlock(CheckboxFieldBlock):

    class Meta:
        label = _('Send Notice')


class DeterminationCustomFormFieldsBlock(CustomFormFieldsBlock):
    char = CharFieldBlock(group=_('Fields'))
    text = TextFieldBlock(group=_('Fields'))
    text_markup = RichTextBlock(group=_('Fields'), label=_('Section text/header'))
    checkbox = CheckboxFieldBlock(group=_('Fields'))
    dropdown = DropdownFieldBlock(group=_('Fields'))
    send_notice = SendNoticeBlock(group=_('Fields'))
    required_blocks = DeterminationMustIncludeFieldBlock.__subclasses__()
