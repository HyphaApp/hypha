"""Application form field blocks that can be marked as personal information.

Only the answers of an application form are ever redacted, see
`AccessFormData.render_answer()`, so the "Personal information" checkbox is
offered on these blocks alone. Review, determination and project forms keep
using the plain field blocks.

The blocks are thin subclasses that add nothing but the checkbox, so they
deconstruct into migrations exactly like the blocks they extend and answer to
the same `isinstance()` checks.
"""

from hypha.apply.categories.blocks import CategoryQuestionBlock
from hypha.apply.stream_forms.blocks import (
    CharFieldBlock,
    CheckboxesFieldBlock,
    CheckboxFieldBlock,
    DateFieldBlock,
    DateTimeFieldBlock,
    DropdownFieldBlock,
    FileFieldBlock,
    ImageFieldBlock,
    MultiFileFieldBlock,
    MultiInputCharFieldBlock,
    NumberFieldBlock,
    PIIFieldMixin,
    RadioButtonsFieldBlock,
    TextFieldBlock,
    TimeFieldBlock,
)
from hypha.apply.utils.blocks import MarkdownTextFieldBlock, RichTextFieldBlock


class PIICharFieldBlock(PIIFieldMixin, CharFieldBlock):
    pass


class PIIMultiInputCharFieldBlock(PIIFieldMixin, MultiInputCharFieldBlock):
    pass


class PIITextFieldBlock(PIIFieldMixin, TextFieldBlock):
    pass


class PIIRichTextFieldBlock(PIIFieldMixin, RichTextFieldBlock):
    pass


class PIIMarkdownTextFieldBlock(PIIFieldMixin, MarkdownTextFieldBlock):
    pass


class PIINumberFieldBlock(PIIFieldMixin, NumberFieldBlock):
    pass


class PIICheckboxFieldBlock(PIIFieldMixin, CheckboxFieldBlock):
    pass


class PIIRadioButtonsFieldBlock(PIIFieldMixin, RadioButtonsFieldBlock):
    pass


class PIIDropdownFieldBlock(PIIFieldMixin, DropdownFieldBlock):
    pass


class PIICheckboxesFieldBlock(PIIFieldMixin, CheckboxesFieldBlock):
    pass


class PIIDateFieldBlock(PIIFieldMixin, DateFieldBlock):
    pass


class PIITimeFieldBlock(PIIFieldMixin, TimeFieldBlock):
    pass


class PIIDateTimeFieldBlock(PIIFieldMixin, DateTimeFieldBlock):
    pass


class PIIImageFieldBlock(PIIFieldMixin, ImageFieldBlock):
    pass


class PIIFileFieldBlock(PIIFieldMixin, FileFieldBlock):
    pass


class PIIMultiFileFieldBlock(PIIFieldMixin, MultiFileFieldBlock):
    pass


class PIICategoryQuestionBlock(PIIFieldMixin, CategoryQuestionBlock):
    pass


def unmarked_block_class(block):
    """The block class a PII-markable block adds the checkbox to.

    Lets code that switches on the exact block class keep working for the
    application form, where the blocks are the subclasses above.
    """
    # `object` ends every MRO and is never a `PIIFieldMixin`, so this always
    # returns: the block's own class for a plain block, the block it extends
    # for one of the subclasses above.
    for block_class in type(block).__mro__:
        if not issubclass(block_class, PIIFieldMixin):
            return block_class
