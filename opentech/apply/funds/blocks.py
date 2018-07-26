from django import forms
from django.utils.translation import ugettext_lazy as _

from addressfield.fields import AddressField
from opentech.apply.categories.blocks import CategoryQuestionBlock
from opentech.apply.stream_forms.blocks import FormFieldsBlock
from opentech.apply.utils.blocks import MustIncludeFieldBlock, CustomFormFieldsBlock


class ApplicationMustIncludeFieldBlock(MustIncludeFieldBlock):
    pass


class TitleBlock(ApplicationMustIncludeFieldBlock):
    name = 'title'
    description = 'The title of the project'


class ValueBlock(ApplicationMustIncludeFieldBlock):
    name = 'value'
    description = 'The value of the project'
    widget = forms.NumberInput


class EmailBlock(ApplicationMustIncludeFieldBlock):
    name = 'email'
    description = 'The applicant email address'
    widget = forms.EmailInput

    class Meta:
        icon = 'mail'


class AddressFieldBlock(ApplicationMustIncludeFieldBlock):
    name = 'address'
    description = 'The postal address of the user'

    field_class = AddressField

    class Meta:
        label = _('Address')
        icon = 'home'


class FullNameBlock(ApplicationMustIncludeFieldBlock):
    name = 'full_name'
    description = 'Full name'

    class Meta:
        icon = 'user'


class ApplicationCustomFormFieldsBlock(CustomFormFieldsBlock, FormFieldsBlock):
    category = CategoryQuestionBlock(group=_('Custom'))
    required_blocks = ApplicationMustIncludeFieldBlock.__subclasses__()


REQUIRED_BLOCK_NAMES = [block.name for block in ApplicationMustIncludeFieldBlock.__subclasses__()]
