import json

from django import forms
from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from hypha.addressfield.fields import ADDRESS_FIELDS_ORDER, AddressField
from hypha.apply.categories.blocks import CategoryQuestionBlock
from hypha.apply.stream_forms.blocks import FormFieldsBlock
from hypha.apply.utils.blocks import (
    CustomFormFieldsBlock,
    MustIncludeFieldBlock,
    RichTextFieldBlock,
    SingleIncludeBlock,
)
from hypha.apply.utils.templatetags.apply_tags import format_number_as_currency


class ApplicationSingleIncludeFieldBlock(SingleIncludeBlock):
    pass


class ApplicationMustIncludeFieldBlock(MustIncludeFieldBlock):
    pass


class TitleBlock(ApplicationMustIncludeFieldBlock):
    name = "title"
    description = "The title of the project"
    field_label = blocks.CharBlock(
        label=_("Label"), default=_("What is the title of your application?")
    )
    help_text = blocks.TextBlock(
        required=False,
        label=_("Help text"),
        default=_("This project name can be changed if a full proposal is requested."),
    )

    class Meta:
        label = _("Application title")
        icon = "tag"


class ValueBlock(ApplicationSingleIncludeFieldBlock):
    name = "value"
    description = "The value of the project"
    widget = forms.NumberInput(attrs={"min": 0})
    field_class = forms.FloatField

    class Meta:
        label = _("Requested amount")
        icon = "decimal"

    def prepare_data(self, value, data, serialize):
        if not data:
            return data
        return format_number_as_currency(str(data))


class OrganizationNameBlock(ApplicationSingleIncludeFieldBlock):
    name = "organization_name"
    description = "The name of the organization"
    widget = forms.TextInput()

    class Meta:
        label = _("Organization name")


class EmailBlock(ApplicationMustIncludeFieldBlock):
    name = "email"
    description = "The applicant email address"
    field_label = blocks.CharBlock(
        label=_("Label"), default=_("What email address should we use to contact you?")
    )
    help_text = blocks.TextBlock(
        required=False,
        label=_("Help text"),
        default=_(
            "We will use this email address to communicate with you about your proposal."
        ),
    )

    widget = forms.EmailInput
    field_class = forms.EmailField

    class Meta:
        icon = "mail"


class AddressFieldBlock(ApplicationSingleIncludeFieldBlock):
    name = "address"
    description = "The postal address of the user"

    field_class = AddressField

    class Meta:
        label = _("Address")
        icon = "home"

    def format_data(self, data):
        # Based on the fields listed in addressfields/widgets.py
        return ", ".join(data[field] for field in ADDRESS_FIELDS_ORDER if data[field])

    def prepare_data(self, value, data, serialize):
        if not data:
            return data
        data = json.loads(data)
        data = {field: data[field] for field in ADDRESS_FIELDS_ORDER}

        if serialize:
            return data

        return ", ".join(value for value in data.values() if value)


class FullNameBlock(ApplicationMustIncludeFieldBlock):
    name = "full_name"
    description = "Full name"
    field_label = blocks.CharBlock(label=_("Label"), default=_("What is your name?"))
    help_text = blocks.TextBlock(
        required=False,
        label=_("Help text"),
        default=_(
            "We will use this name when we communicate with you about your proposal."
        ),
    )

    class Meta:
        label = _("Full name")
        icon = "user"


class DurationBlock(ApplicationSingleIncludeFieldBlock):
    name = "duration"
    description = "Duration"

    DAYS = "days"
    WEEKS = "weeks"
    MONTHS = "months"
    DURATION_TYPE_CHOICES = ((DAYS, "Days"), (WEEKS, "Weeks"), (MONTHS, "Months"))
    DURATION_DAY_OPTIONS = {
        1: "1 day",
        2: "2 days",
        3: "3 days",
        4: "4 days",
        5: "5 days",
        6: "6 days",
        7: "7 days",
    }
    DURATION_WEEK_OPTIONS = {
        1: "1 week",
        2: "2 weeks",
        3: "3 weeks",
        4: "4 weeks",
        5: "5 weeks",
        6: "6 weeks",
        7: "7 weeks",
        8: "8 weeks",
        9: "9 weeks",
        10: "10 weeks",
        11: "11 weeks",
        12: "12 weeks",
    }
    DURATION_MONTH_OPTIONS = {
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
    duration_type = blocks.ChoiceBlock(
        help_text=(
            "Duration type is used to display duration choices in Days, Weeks or Months in application forms. "
            "Be careful, changing the duration type in the active round can result in data inconsistency."
        ),
        choices=DURATION_TYPE_CHOICES,
        default=MONTHS,
    )

    def get_field_kwargs(self, struct_value, *args, **kwargs):
        field_kwargs = super().get_field_kwargs(struct_value, *args, **kwargs)
        if struct_value["duration_type"] == self.DAYS:
            field_kwargs["choices"] = self.DURATION_DAY_OPTIONS.items()
        elif struct_value["duration_type"] == self.WEEKS:
            field_kwargs["choices"] = self.DURATION_WEEK_OPTIONS.items()
        else:
            field_kwargs["choices"] = self.DURATION_MONTH_OPTIONS.items()
        return field_kwargs

    def prepare_data(self, value, data, serialize):
        if not data:
            return data
        if value["duration_type"] == self.DAYS:
            return self.DURATION_DAY_OPTIONS[int(data)]
        if value["duration_type"] == self.WEEKS:
            return self.DURATION_WEEK_OPTIONS[int(data)]
        return self.DURATION_MONTH_OPTIONS[int(data)]

    class Meta:
        icon = "date"


class ApplicationCustomFormFieldsBlock(CustomFormFieldsBlock, FormFieldsBlock):
    category = CategoryQuestionBlock(group=_("Custom"))
    rich_text = RichTextFieldBlock(group=_("Fields"))
    required_blocks = ApplicationMustIncludeFieldBlock.__subclasses__()
    single_blocks = ApplicationSingleIncludeFieldBlock.__subclasses__()


REQUIRED_BLOCK_NAMES = [
    block.name for block in ApplicationMustIncludeFieldBlock.__subclasses__()
]

SINGLE_BLOCK_NAMES = [
    block.name for block in ApplicationSingleIncludeFieldBlock.__subclasses__()
]

NAMED_BLOCKS = REQUIRED_BLOCK_NAMES + SINGLE_BLOCK_NAMES
