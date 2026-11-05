from collections import Counter

import nh3
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from wagtail.admin import messages
from wagtail.blocks import (
    ListBlock,
    StaticBlock,
    StreamBlock,
    StreamBlockValidationError,
    StructBlockValidationError,
)

from hypha.apply.stream_forms.blocks import (
    FormFieldBlock,
    OptionalFormFieldBlock,
    TextFieldBlock,
)
from hypha.apply.utils.options import RICH_TEXT_WIDGET
from hypha.core.widgets import PagedownWidget


def find_duplicates(items):
    counted = Counter(items)
    duplicates = [name for name, count in counted.items() if count > 1]
    return duplicates


def prettify_names(sequence):
    return [nice_field_name(item) for item in sequence]


def nice_field_name(name):
    return name.title().replace("_", " ")


def show_admin_form_error_messages(request, form):
    for errors in form.errors.as_data().values():
        for error in errors:
            # Errors on individual blocks are displayed in the StreamField editor.
            # A message is still needed, it holds Wagtail's "Go to the first error" button.
            if isinstance(error, StreamBlockValidationError):
                error_messages = error.non_block_errors or [
                    _("Please correct the errors on the highlighted fields.")
                ]
            else:
                error_messages = error.messages
            for error_message in error_messages:
                messages.error(request, error_message)


class RichTextFieldBlock(TextFieldBlock):
    widget = RICH_TEXT_WIDGET

    class Meta:
        label = _("Rich text field")
        icon = "form"

    def get_searchable_content(self, value, data):
        return nh3.clean(data or "", tags=set())

    def no_response(self):
        return "<p>-</p>"


class MarkdownTextFieldBlock(TextFieldBlock):
    widget = PagedownWidget()
    template = ""

    class Meta:
        label = _("Markdown text field")
        icon = "form"
        template = "stream_forms/render_markdown_field.html"

    def get_searchable_content(self, value, data):
        return nh3.clean(data or "", tags=set())

    def no_response(self):
        return "<p>-</p>"


class CustomFormFieldsBlock(StreamBlock):
    rich_text = RichTextFieldBlock(group=_("Fields"))
    markdown_text = MarkdownTextFieldBlock(group=_("Fields"))
    required_blocks = []
    single_blocks = []

    def __init__(self, *args, **kwargs):
        # The space before " Required" is to make the group sort first. Ugly but easy, and it works.
        child_blocks = [
            (block.name, block(group=_(" Required"))) for block in self.required_blocks
        ]
        child_blocks += [
            (block.name, block(group=_("Custom"))) for block in self.single_blocks
        ]
        self.required_block_names = [block.name for block in self.required_blocks]
        self.single_block_names = [
            block.name for block in self.single_blocks
        ] + self.required_block_names

        super().__init__(child_blocks, *args, **kwargs)

    def clean(self, value):
        block_errors = {}
        all_errors = []
        try:
            value = super().clean(value)
        except StreamBlockValidationError as e:
            block_errors = e.block_errors
            all_errors = list(e.non_block_errors)

        block_types = [block.block_type for block in value]
        missing = set(self.required_block_names) - set(block_types)

        duplicates = [
            name
            for name in find_duplicates(block_types)
            if name in self.single_block_names
        ]

        # Wagtail sets is_deferred_validation when saving drafts, required checks are skipped then.
        if missing and not self.is_deferred_validation:
            all_errors.append(
                _("You are missing the following required fields: {}").format(
                    ", ".join(prettify_names(missing))
                )
            )

        if duplicates:
            all_errors.append(
                _("The following fields must be included only once: {}").format(
                    ", ".join(prettify_names(duplicates))
                )
            )
            for i, block_name in enumerate(block_types):
                if block_name in duplicates:
                    self.add_error_to_child(block_errors, i, _("Duplicate field"))

        for block in value:
            if self.is_deferred_validation:
                break
            if hasattr(block.block, "child_blocks"):
                for child_block_name, child_block in block.block.child_blocks.items():
                    if child_block.required and not block.value[child_block_name]:
                        all_errors.append(
                            _("{child} cannot be empty for {parent}").format(
                                child=child_block.label, parent=block.block.label
                            )
                        )
                    if (
                        isinstance(child_block, ListBlock)
                        and child_block.child_block.required
                    ):
                        for child_value in block.value[child_block_name]:
                            if not child_value:
                                all_errors.append(
                                    _("{child} cannot be empty for {parent}").format(
                                        child=child_block.label,
                                        parent=block.block.label,
                                    )
                                )

        if all_errors or block_errors:
            raise StreamBlockValidationError(
                block_errors=block_errors, non_block_errors=all_errors
            )

        return value

    def add_error_to_child(self, errors, child_number, message):
        error = errors.setdefault(child_number, StructBlockValidationError())
        error.non_block_errors.append(message)

    # Activate if/when needed.
    #
    # def to_python(self, value):
    #     """
    #     This allows historic data to still be accessible even
    #     if a custom field type is removed from the code in the future.
    #     """
    #     # Only the JSON-ish form holds stored data, Wagtail also calls this with
    #     # StreamValues, tuples, strings and None, leave those to the default.
    #     if isinstance(value, list):
    #         # If the data type is missing, fallback to a CharField. Blocks without
    #         # a struct value are markup that hold no answers, the default drops them.
    #         value = [
    #             {**child_data, "type": "char"}
    #             if isinstance(child_data, dict)
    #             and child_data["type"] not in self.child_blocks
    #             and isinstance(child_data.get("value"), dict)
    #             else child_data
    #             for child_data in value
    #         ]

    #     return super().to_python(value)


class SingleIncludeStatic(StaticBlock):
    """Helper block which displays additional information about the must include block and
    helps display the error in a noticeable way.
    """

    def __init__(self, *args, description="", **kwargs):
        self.description = description
        super().__init__(*args, **kwargs)

    class Meta:
        admin_text = _("Must be included in the form only once.")

    def render_form(self, *args, **kwargs):
        errors = kwargs.pop("errors")
        if errors:
            # Pretend the error is a readonly input so that we get nice formatting
            # Issue discussed here: https://github.com/wagtail/wagtail/issues/4122
            error_message = (
                '<div class="error"><input readonly placeholder="{}"></div>'.format(
                    errors[0]
                )
            )
        else:
            error_message = ""
        form = super().render_form(*args, **kwargs)
        form = "<br>".join([self.description, form]) + error_message
        return mark_safe(form)

    def deconstruct(self):
        return ("wagtail.blocks.static_block.StaticBlock", (), {})


class SingleIncludeMixin:
    def __init__(self, *args, **kwargs):
        info_name = _("{} Field").format(
            self._meta_class.label if self._meta_class.label else self.name.title()
        )
        child_blocks = [
            ("info", SingleIncludeStatic(label=info_name, description=self.description))
        ]
        super().__init__(child_blocks, *args, **kwargs)


class SingleIncludeBlock(SingleIncludeMixin, OptionalFormFieldBlock):
    """A block that is only allowed to be included once in the form, but is optional"""


class MustIncludeFieldBlock(SingleIncludeMixin, FormFieldBlock):
    """Any block inheriting from this will need to be included in the application forms
    This data will also be available to query on the submission object
    """

    def get_field_kwargs(self, struct_value):
        kwargs = super().get_field_kwargs(struct_value)
        kwargs["required"] = True
        return kwargs
