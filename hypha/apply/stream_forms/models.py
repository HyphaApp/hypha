# Credit to https://github.com/BertrandBordage for initial implementation
import copy
from collections import OrderedDict

from django.utils.translation import gettext_lazy as _
from wagtail.contrib.forms.models import AbstractForm

from hypha.apply.funds.blocks import (
    ApplicationMustIncludeFieldBlock,
    EmailBlock,
    FullNameBlock,
)

from .blocks import (
    FormFieldBlock,
    GroupToggleBlock,
    GroupToggleEndBlock,
    MultiInputCharFieldBlock,
    TextFieldBlock,
)
from .forms import BlockFieldWrapper, PageStreamBaseForm


class BaseStreamForm:
    """Base class for creating dynamic forms using Wagtail StreamField.

    This class provides functionality for handling form field definitions,
    form data serialization/deserialization, and form generation.
    """

    submission_form_class = PageStreamBaseForm
    wagtail_reference_index_ignore = True

    @classmethod
    def from_db(cls, db, field_names, values):
        """Deserialize form data when loading from database.

        Args:
            db: Database connection
            field_names: List of field names being loaded
            values: Values for the fields

        Returns:
            Instance with deserialized form data
        """
        instance = super().from_db(db, field_names, values)
        if "form_data" in field_names:
            instance.form_data = cls.deserialize_form_data(
                instance, instance.form_data, instance.form_fields
            )
        return instance

    @classmethod
    def deserialize_form_data(cls, instance, form_data, form_fields):
        """Convert stored form data back into Python objects.

        Args:
            instance: Form instance
            form_data: Raw form data from database
            form_fields: Form field definitions

        Returns:
            Deserialized form data
        """
        data = form_data.copy()
        # PERFORMANCE NOTE:
        # Do not attempt to iterate over form_fields - that will fully instantiate the form_fields
        # including any sub queries that they do
        for _i, field_data in enumerate(form_fields.raw_data):
            block = form_fields.stream_block.child_blocks[field_data["type"]]
            field_id = field_data.get("id")
            try:
                value = data[field_id]
            except KeyError:
                pass
            else:
                data[field_id] = block.decode(value)
        return data

    def get_defined_fields(self):
        """Get the form field definitions.

        Returns:
            StreamField containing form field blocks

        Raises:
            AttributeError: If form_fields attribute is not defined on instance
        """
        try:
            return self.form_fields  # type: ignore
        except AttributeError as err:
            raise AttributeError(
                "form_fields attribute not found. "
                "Make sure form_fields is defined on the implementing class."
            ) from err

    def get_form_fields(self, draft=False, form_data=None, user=None):
        """Generate form fields with applied logic and grouping.

        Args:
            draft: Whether this is a draft form. When True, fields that are not
                  marked as ApplicationMustIncludeFieldBlock will have their
                  required flag set to False, allowing incomplete form submissions
                  to be saved as drafts.
            form_data: Existing form data
            user: User completing the form

        Returns:
            OrderedDict of form fields
        """
        if form_data is None:
            form_data = {}

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
                disabled_help_text = _(
                    "You are logged in so this information is fetched from your user account."
                )
                if isinstance(block, FullNameBlock) and user and user.is_authenticated:
                    if user.full_name:
                        field_from_block.disabled = True
                        field_from_block.initial = user.full_name
                        field_from_block.help_text = disabled_help_text
                    else:
                        field_from_block.help_text = _(
                            "You are logged in but your user account does not have a "
                            "full name. We'll update your user account with the name you provide here."
                        )
                if isinstance(block, EmailBlock) and user and user.is_authenticated:
                    field_from_block.disabled = True
                    field_from_block.initial = user.email
                    field_from_block.help_text = disabled_help_text
                if draft and not issubclass(
                    block.__class__, ApplicationMustIncludeFieldBlock
                ):
                    field_from_block.required = False
                field_from_block.group_number = group_counter if is_in_group else 1
                if isinstance(block, GroupToggleBlock) and not is_in_group:
                    field_from_block.group_number = 1
                    field_from_block.grouper_for = group_counter + 1
                    group_counter += 1
                    is_in_group = True
                    grouped_fields_visible = (
                        form_data.get(struct_child.id) == field_from_block.choices[0][0]
                    )
                if isinstance(block, TextFieldBlock):
                    field_from_block.word_limit = struct_value.get("word_limit")
                if isinstance(block, MultiInputCharFieldBlock):
                    number_of_inputs = struct_value.get("number_of_inputs")
                    for index in range(number_of_inputs):
                        form_fields[struct_child.id + "_" + str(index)] = (
                            field_from_block
                        )
                        field_from_block.multi_input_id = struct_child.id
                        field_from_block.add_button_text = struct_value.get(
                            "add_button_text"
                        )
                        if (
                            index == number_of_inputs - 1
                        ):  # Add button after last input field
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
                        field_from_block.required_when_visible = (
                            field_from_block.required
                        )
                        field_from_block.required = (
                            field_from_block.required & grouped_fields_visible
                        )
                        field_from_block.visible = grouped_fields_visible
                    form_fields[struct_child.id] = field_from_block
            elif isinstance(block, GroupToggleEndBlock):
                # Group toggle end block is used only to group fields and not used in actual form.
                # Todo: Use streamblock to create nested form field blocks, a more elegant method to group form fields.
                is_in_group = False
            else:
                field_wrapper = BlockFieldWrapper(struct_child)
                field_wrapper.group_number = group_counter if is_in_group else 1
                form_fields[struct_child.id] = field_wrapper

        return form_fields

    def get_form_class(self, draft=False, form_data=None, user=None):
        """Dynamically creates and returns a form class based on the field configuration.

        Creates a new form class that inherits from submission_form_class (PageStreamBaseForm)
        and includes all the dynamically generated form fields.

        Args:
            draft: Whether this is a draft form
            form_data: Existing form data for pre-populating form fields
            user: User completing the form, used for auto-populating user fields.

        Returns:
            A dynamically generated form class
        """
        return type(
            "WagtailStreamForm",
            (self.submission_form_class,),
            self.get_form_fields(draft=draft, form_data=form_data, user=user),
        )


class AbstractStreamForm(BaseStreamForm, AbstractForm):
    """Abstract base class for stream forms.

    Combines BaseStreamForm functionality with Wagtail's AbstractForm.
    """

    class Meta:
        abstract = True
