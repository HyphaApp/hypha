import json

from django import forms
from django.utils.translation import ugettext_lazy as _

from addressfield.fields import AddressField
from opentech.apply.categories.blocks import CategoryQuestionBlock
from opentech.apply.stream_forms.blocks import FormFieldsBlock
from opentech.apply.utils.blocks import (
    CustomFormFieldsBlock,
    MustIncludeFieldBlock,
    RichTextFieldBlock,
    SingleIncludeBlock,
)


class ApplicationSingleIncludeFieldBlock(SingleIncludeBlock):
    pass


class ApplicationMustIncludeFieldBlock(MustIncludeFieldBlock):
    pass


class TitleBlock(ApplicationMustIncludeFieldBlock):
    name = 'title'
    description = 'The title of the project'

    class Meta:
        label = _('Application title')
        icon = 'tag'


class ValueBlock(ApplicationSingleIncludeFieldBlock):
    name = 'value'
    description = 'The value of the project'
    widget = forms.NumberInput

    class Meta:
        label = _('Requested amount')


class EmailBlock(ApplicationMustIncludeFieldBlock):
    name = 'email'
    description = 'The applicant email address'
    widget = forms.EmailInput
    field_class = forms.EmailField

    class Meta:
        icon = 'mail'


class AddressFieldBlock(ApplicationSingleIncludeFieldBlock):
    name = 'address'
    description = 'The postal address of the user'

    field_class = AddressField

    class Meta:
        label = _('Address')
        icon = 'home'

    def format_data(self, data):
        # Based on the fields listed in addressfields/widgets.py
        order_fields = [
            'thoroughfare', 'premise', 'localityname', 'administrativearea', 'postalcode', 'country'
        ]
        address = json.loads(data)
        return ', '.join(
            address[field]
            for field in order_fields
            if address[field]
        )

    def prepare_data(self, value, data, serialize):
        if serialize:
            return json.loads(data)
        return data


class FullNameBlock(ApplicationMustIncludeFieldBlock):
    name = 'full_name'
    description = 'Full name'

    class Meta:
        icon = 'user'


class DurationBlock(ApplicationMustIncludeFieldBlock):
    name = 'duration'
    description = 'Duration'

    DURATION_OPTIONS = {
        1: "1 month",
        2: "2 months",
        3: "3 months",
        4: "4 months",
        5: "5 months",
        6: "6 months",
        7: "7 months",
        8: "8 months",
        9: "9 months",
        10: "10 months",
        11: "11 months",
        12: "12 months",
        18: "18 months",
        24: "24 months",
    }
    field_class = forms.ChoiceField

    def get_field_kwargs(self, *args, **kwargs):
        field_kwargs = super().get_field_kwargs(*args, **kwargs)
        field_kwargs['choices'] = self.DURATION_OPTIONS.items()
        return field_kwargs

    def format_data(self, data):
        return self.DURATION_OPTIONS[int(data)]

    class Meta:
        icon = 'date'


class ApplicationCustomFormFieldsBlock(CustomFormFieldsBlock, FormFieldsBlock):
    category = CategoryQuestionBlock(group=_('Custom'))
    rich_text = RichTextFieldBlock(group=_('Fields'))
    required_blocks = ApplicationMustIncludeFieldBlock.__subclasses__()
    single_blocks = ApplicationSingleIncludeFieldBlock.__subclasses__()


REQUIRED_BLOCK_NAMES = [block.name for block in ApplicationMustIncludeFieldBlock.__subclasses__()]

SINGLE_BLOCK_NAMES = [block.name for block in ApplicationSingleIncludeFieldBlock.__subclasses__()]

NAMED_BLOCKS = REQUIRED_BLOCK_NAMES + SINGLE_BLOCK_NAMES
