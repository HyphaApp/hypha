# Credit to https://github.com/BertrandBordage for initial implementation
import copy
from collections import OrderedDict

from wagtail.contrib.forms.models import AbstractForm

from hypha.apply.funds.blocks import ApplicationMustIncludeFieldBlock

from .blocks import (
    FormFieldBlock,
    GroupToggleBlock,
    GroupToggleEndBlock,
    MultiInputCharFieldBlock,
    TextFieldBlock,
)
from .forms import BlockFieldWrapper, PageStreamBaseForm


class BaseStreamForm:
    submission_form_class = PageStreamBaseForm

    @classmethod
    def from_db(cls, db, field_names, values):
        instance = super().from_db(db, field_names, values)
        if 'form_data' in field_names:
            instance.form_data = cls.deserialize_form_data(instance, instance.form_data, instance.form_fields)
        return instance

    @classmethod
    def deserialize_form_data(cls, instance, form_data, form_fields):
        data = form_data.copy()
        # PERFORMANCE NOTE:
        # Do not attempt to iterate over form_fields - that will fully instantiate the form_fields
        # including any sub queries that they do
        for i, field_data in enumerate(form_fields.raw_data):
            block = form_fields.stream_block.child_blocks[field_data['type']]
            field_id = field_data.get('id')
            try:
                value = data[field_id]
            except KeyError:
                pass
            else:
                data[field_id] = block.decode(value)
        return data

    def get_defined_fields(self):
        return self.form_fields

    def get_form_fields(self, draft=False, form_data={}):
        form_fields = OrderedDict()
        field_blocks = self.get_defined_fields()
        group_counter = 1
        is_in_group = False

        # If true option 1 is selected
        grouped_fields_visible = False
        for struct_child in field_blocks:
            block = struct_child.block
            struct_value = struct_child.value
            if isinstance(block, FormFieldBlock):
                field_from_block = block.get_field(struct_value)
                field_from_block.canonical_name = block.name
                if draft and not issubclass(block.__class__, ApplicationMustIncludeFieldBlock):
                    field_from_block.required = False
                field_from_block.help_link = struct_value.get('help_link')
                field_from_block.group_number = group_counter if is_in_group else 1
                if isinstance(block, GroupToggleBlock) and not is_in_group:
                    field_from_block.group_number = 1
                    field_from_block.grouper_for = group_counter + 1
                    group_counter += 1
                    is_in_group = True
                    grouped_fields_visible = form_data.get(struct_child.id) == field_from_block.choices[0][0]
                if isinstance(block, TextFieldBlock):
                    field_from_block.word_limit = struct_value.get('word_limit')
                if isinstance(block, MultiInputCharFieldBlock):
                    number_of_inputs = struct_value.get('number_of_inputs')
                    for index in range(number_of_inputs):
                        form_fields[struct_child.id + '_' + str(index)] = field_from_block
                        field_from_block.multi_input_id = struct_child.id
                        field_from_block.add_button_text = struct_value.get('add_button_text')
                        if index == number_of_inputs - 1:  # Add button after last input field
                            field_from_block.multi_input_add_button = True
                            # Index for field until which fields will be visible to applicant.
                            # Initially only the first field with id UUID_0 will be visible.
                            field_from_block.visibility_index = 0
                            field_from_block.max_index = index
                        if index != 0:
                            field_from_block.multi_input_field = True
                            field_from_block.required = False
                            field_from_block.initial = None
                        field_from_block = copy.copy(field_from_block)
                else:
                    if is_in_group and not isinstance(block, GroupToggleBlock):
                        field_from_block.required_when_visible = field_from_block.required
                        field_from_block.required = field_from_block.required & grouped_fields_visible
                        field_from_block.visible = grouped_fields_visible
                    form_fields[struct_child.id] = field_from_block
            elif isinstance(block, GroupToggleEndBlock):
                # Group toogle end block is used only to group fields and not used in actual form.
                # Todo: Use streamblock to create nested form field blocks, a more elegant method to group form fields.
                is_in_group = False
            else:
                field_wrapper = BlockFieldWrapper(struct_child)
                field_wrapper.canonical_name = block.name
                field_wrapper.group_number = group_counter if is_in_group else 1
                form_fields[struct_child.id] = field_wrapper

        return form_fields

    def get_form_class(self, draft=False, form_data={}):
        return type('WagtailStreamForm', (self.submission_form_class,), self.get_form_fields(draft, form_data))


class AbstractStreamForm(BaseStreamForm, AbstractForm):
    class Meta:
        abstract = True
