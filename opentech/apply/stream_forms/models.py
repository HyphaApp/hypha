# Credit to https://github.com/BertrandBordage for initial implementation
from collections import OrderedDict

from wagtail.contrib.forms.models import AbstractForm

from .blocks import FormFieldBlock, GroupToggleBlock, GroupToggleEndBlock
from .forms import BlockFieldWrapper, PageStreamBaseForm


class BaseStreamForm:
    submission_form_class = PageStreamBaseForm

    def get_defined_fields(self):
        return self.form_fields

    def get_form_fields(self):
        form_fields = OrderedDict()
        field_blocks = self.get_defined_fields()
        group_counter = 1
        is_in_group = False
        for struct_child in field_blocks:
            block = struct_child.block
            struct_value = struct_child.value

            if isinstance(block, FormFieldBlock):
                field_from_block = block.get_field(struct_value)
                field_from_block.help_link = struct_value.get('help_link')
                field_from_block.group_number = group_counter if is_in_group else 1
                if isinstance(block, GroupToggleBlock) and not is_in_group:
                    field_from_block.group_number = 1
                    field_from_block.grouper_for = group_counter + 1
                    group_counter += 1
                    is_in_group = True
                form_fields[struct_child.id] = field_from_block
            elif isinstance(block, GroupToggleEndBlock):
                # Group toogle end block is used only to group fields and not used in actual form.
                # Todo: Use streamblock to create nested form field blocks, a more elegant method to group form fields.
                is_in_group = False
            else:
                field_wrapper = BlockFieldWrapper(struct_child)
                field_wrapper.group_number = group_counter if is_in_group else 1
                form_fields[struct_child.id] = field_wrapper

        return form_fields

    def get_form_class(self):
        return type('WagtailStreamForm', (self.submission_form_class,), self.get_form_fields())


class AbstractStreamForm(BaseStreamForm, AbstractForm):
    class Meta:
        abstract = True
