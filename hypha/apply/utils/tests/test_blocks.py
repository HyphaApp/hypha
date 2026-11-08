from django.core.exceptions import ValidationError
from django.test import SimpleTestCase
from wagtail.blocks import StreamBlockValidationError

from hypha.apply.funds.blocks import ApplicationCustomFormFieldsBlock
from hypha.apply.projects.blocks import ProjectFormCustomFormFieldsBlock
from hypha.apply.stream_forms.blocks import CharFieldBlock


def char_block(**kwargs):
    return {
        "type": "char",
        "value": {"field_label": "Label", **kwargs},
    }


def title_block():
    return {"type": "title", "value": {"field_label": "Title"}}


class TestCustomFormFieldsBlockClean(SimpleTestCase):
    def clean_errors(self, block, data):
        with self.assertRaises(StreamBlockValidationError) as cm:
            block.clean(block.to_python(data))
        return cm.exception

    def test_valid_value_is_returned_cleaned(self):
        block = ProjectFormCustomFormFieldsBlock()
        value = block.clean(block.to_python([char_block()]))
        self.assertEqual(value[0].block_type, "char")
        self.assertIsInstance(value[0].block, CharFieldBlock)

    def test_child_block_errors_are_kept(self):
        error = self.clean_errors(
            ProjectFormCustomFormFieldsBlock(),
            [char_block(), char_block(format="not-a-valid-choice")],
        )
        self.assertEqual(list(error.block_errors), [1])
        self.assertIn("format", error.block_errors[1].block_errors)

    def test_empty_required_stream_is_invalid(self):
        error = self.clean_errors(ProjectFormCustomFormFieldsBlock(), [])
        self.assertEqual(list(error.non_block_errors), ["This field is required."])

    def test_missing_required_blocks_are_reported(self):
        error = self.clean_errors(ApplicationCustomFormFieldsBlock(), [title_block()])
        self.assertEqual(len(error.non_block_errors), 1)
        self.assertIn(
            "You are missing the following required fields",
            error.non_block_errors[0],
        )

    def test_duplicates_are_marked_on_each_block(self):
        error = self.clean_errors(
            ApplicationCustomFormFieldsBlock(),
            [title_block(), char_block(), title_block()],
        )
        self.assertIn(
            "The following fields must be included only once: Title",
            list(error.non_block_errors),
        )
        self.assertEqual(sorted(error.block_errors), [0, 2])
        self.assertEqual(
            error.as_json_data()["blockErrors"][2]["messages"], ["Duplicate field"]
        )

    def test_duplicate_mark_is_added_to_existing_block_errors(self):
        block = ApplicationCustomFormFieldsBlock()
        error = self.clean_errors(
            block,
            [title_block(), {"type": "title", "value": {"field_label": ""}}],
        )
        block_error = error.as_json_data()["blockErrors"][1]
        self.assertEqual(block_error["messages"], ["Duplicate field"])
        self.assertIn("field_label", block_error["blockErrors"])

    def test_duplicate_mark_keeps_plain_child_error(self):
        errors = {0: ValidationError("Bad")}
        ApplicationCustomFormFieldsBlock().add_error_to_child(
            errors, 0, "Duplicate field"
        )
        self.assertEqual(
            errors[0].as_json_data()["messages"], ["Bad", "Duplicate field"]
        )

    def test_empty_child_label_is_reported_on_the_block(self):
        error = self.clean_errors(
            ProjectFormCustomFormFieldsBlock(), [char_block(field_label="")]
        )
        self.assertEqual(list(error.non_block_errors), [])
        self.assertIn("field_label", error.block_errors[0].block_errors)
