import json

from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext_lazy
from wagtail import blocks

from hypha.addressfield.fields import ADDRESS_FIELDS_ORDER, AddressField
from hypha.apply.categories.blocks import CategoryQuestionBlock
from hypha.apply.stream_forms.blocks import FormFieldsBlock
from hypha.apply.users.models import User
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
    description = _("The title of the project")
    field_label = blocks.CharBlock(
        label=_("Label"), default=_("What is the title of your application?")
    )
    help_text = blocks.RichTextBlock(
        required=False,
        label=_("Help text"),
        default=_("This project name can be changed if a full proposal is requested."),
    )
    max_length = blocks.IntegerBlock(required=False, label=_("Max length"))

    class Meta:
        label = _("Application title")
        icon = "tag"

    def get_field_kwargs(self, struct_value):
        kwargs = super().get_field_kwargs(struct_value)
        kwargs["max_length"] = struct_value["max_length"]
        return kwargs


class ValueBlock(ApplicationSingleIncludeFieldBlock):
    name = "value"
    description = _("The value of the project")
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
    description = _("The name of the organization")
    widget = forms.TextInput()

    class Meta:
        label = _("Organization name")


class EmailBlock(ApplicationMustIncludeFieldBlock):
    name = "email"
    description = _("The applicant email address")
    field_label = blocks.CharBlock(
        label=_("Label"), default=_("What email address should we use to contact you?")
    )
    help_text = blocks.RichTextBlock(
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
    description = _("The postal address of the user")

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
    description = _("Full name")
    field_label = blocks.CharBlock(label=_("Label"), default=_("What is your name?"))
    help_text = blocks.RichTextBlock(
        required=False,
        label=_("Help text"),
        default=_(
            "We will use this name when we communicate with you about your proposal."
        ),
    )

    def get_field_kwargs(self, struct_value):
        kwargs = super().get_field_kwargs(struct_value)
        # Pull the max length from the full_name db field
        kwargs["max_length"] = User._meta.get_field("full_name").max_length
        return kwargs

    class Meta:
        label = _("Full name")
        icon = "user"


class DurationBlock(ApplicationSingleIncludeFieldBlock):
    name = "duration"
    description = _("Duration")

    DAYS = "days"
    WEEKS = "weeks"
    MONTHS = "months"
    DURATION_TYPE_CHOICES = (
        (DAYS, _("Days")),
        (WEEKS, _("Weeks")),
        (MONTHS, _("Months")),
    )
    DURATION_DAY_OPTIONS = {
        i: ngettext_lazy("{} day", "{} days", i).format(i) for i in range(1, 8)
    }
    DURATION_WEEK_OPTIONS = {
        i: ngettext_lazy("{} week", "{} weeks", i).format(i) for i in range(1, 13)
    }
    DURATION_MONTH_OPTIONS = {
        i: ngettext_lazy("{} month", "{} months", i).format(i)
        for i in [*range(1, 13), 18, 24, 36]
    }
    field_class = forms.ChoiceField
    duration_type = blocks.ChoiceBlock(
        help_text=_(
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
