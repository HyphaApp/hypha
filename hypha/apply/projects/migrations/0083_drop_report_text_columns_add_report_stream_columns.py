# Generated by Django 3.2.23 on 2024-01-23 17:31
# Edited by jbickel@opentechstrategies.com 2024-01-23 to rebase on main

from django.db import migrations, models
import hypha.apply.stream_forms.blocks
import hypha.apply.stream_forms.files
import wagtail.blocks
import wagtail.fields


class Migration(migrations.Migration):
    dependencies = [
        ("application_projects", "0082_projectreportform"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="reportversion",
            name="private_content",
        ),
        migrations.RemoveField(
            model_name="reportversion",
            name="public_content",
        ),
        migrations.AddField(
            model_name="reportversion",
            name="form_data",
            field=models.JSONField(
                default=dict,
                encoder=hypha.apply.stream_forms.files.StreamFieldDataEncoder,
            ),
        ),
        migrations.AddField(
            model_name="reportversion",
            name="form_fields",
            field=wagtail.fields.StreamField(
                [
                    (
                        "text_markup",
                        wagtail.blocks.RichTextBlock(group="Custom", label="Paragraph"),
                    ),
                    (
                        "header_markup",
                        wagtail.blocks.StructBlock(
                            [
                                (
                                    "heading_text",
                                    wagtail.blocks.CharBlock(
                                        form_classname="title", required=True
                                    ),
                                ),
                                (
                                    "size",
                                    wagtail.blocks.ChoiceBlock(
                                        choices=[
                                            ("h2", "H2"),
                                            ("h3", "H3"),
                                            ("h4", "H4"),
                                        ]
                                    ),
                                ),
                            ],
                            group="Custom",
                            label="Section header",
                        ),
                    ),
                    (
                        "char",
                        wagtail.blocks.StructBlock(
                            [
                                (
                                    "field_label",
                                    wagtail.blocks.CharBlock(label="Label"),
                                ),
                                (
                                    "help_text",
                                    wagtail.blocks.RichTextBlock(
                                        label="Help text", required=False
                                    ),
                                ),
                                (
                                    "required",
                                    wagtail.blocks.BooleanBlock(
                                        label="Required", required=False
                                    ),
                                ),
                                (
                                    "format",
                                    wagtail.blocks.ChoiceBlock(
                                        choices=[("email", "Email"), ("url", "URL")],
                                        label="Format",
                                        required=False,
                                    ),
                                ),
                                (
                                    "default_value",
                                    wagtail.blocks.CharBlock(
                                        label="Default value", required=False
                                    ),
                                ),
                            ],
                            group="Fields",
                        ),
                    ),
                    (
                        "multi_inputs_char",
                        wagtail.blocks.StructBlock(
                            [
                                (
                                    "field_label",
                                    wagtail.blocks.CharBlock(label="Label"),
                                ),
                                (
                                    "help_text",
                                    wagtail.blocks.RichTextBlock(
                                        label="Help text", required=False
                                    ),
                                ),
                                (
                                    "required",
                                    wagtail.blocks.BooleanBlock(
                                        label="Required", required=False
                                    ),
                                ),
                                (
                                    "format",
                                    wagtail.blocks.ChoiceBlock(
                                        choices=[("email", "Email"), ("url", "URL")],
                                        label="Format",
                                        required=False,
                                    ),
                                ),
                                (
                                    "default_value",
                                    wagtail.blocks.CharBlock(
                                        label="Default value", required=False
                                    ),
                                ),
                                (
                                    "number_of_inputs",
                                    wagtail.blocks.IntegerBlock(
                                        default=2, label="Max number of inputs"
                                    ),
                                ),
                                (
                                    "add_button_text",
                                    wagtail.blocks.CharBlock(
                                        default="Add new item", required=False
                                    ),
                                ),
                            ],
                            group="Fields",
                        ),
                    ),
                    (
                        "text",
                        wagtail.blocks.StructBlock(
                            [
                                (
                                    "field_label",
                                    wagtail.blocks.CharBlock(label="Label"),
                                ),
                                (
                                    "help_text",
                                    wagtail.blocks.RichTextBlock(
                                        label="Help text", required=False
                                    ),
                                ),
                                (
                                    "required",
                                    wagtail.blocks.BooleanBlock(
                                        label="Required", required=False
                                    ),
                                ),
                                (
                                    "default_value",
                                    wagtail.blocks.TextBlock(
                                        label="Default value", required=False
                                    ),
                                ),
                                (
                                    "word_limit",
                                    wagtail.blocks.IntegerBlock(
                                        default=1000, label="Word limit"
                                    ),
                                ),
                            ],
                            group="Fields",
                        ),
                    ),
                    (
                        "number",
                        wagtail.blocks.StructBlock(
                            [
                                (
                                    "field_label",
                                    wagtail.blocks.CharBlock(label="Label"),
                                ),
                                (
                                    "help_text",
                                    wagtail.blocks.RichTextBlock(
                                        label="Help text", required=False
                                    ),
                                ),
                                (
                                    "required",
                                    wagtail.blocks.BooleanBlock(
                                        label="Required", required=False
                                    ),
                                ),
                                (
                                    "default_value",
                                    wagtail.blocks.CharBlock(
                                        label="Default value", required=False
                                    ),
                                ),
                            ],
                            group="Fields",
                        ),
                    ),
                    (
                        "checkbox",
                        wagtail.blocks.StructBlock(
                            [
                                (
                                    "field_label",
                                    wagtail.blocks.CharBlock(label="Label"),
                                ),
                                (
                                    "help_text",
                                    wagtail.blocks.RichTextBlock(
                                        label="Help text", required=False
                                    ),
                                ),
                                (
                                    "required",
                                    wagtail.blocks.BooleanBlock(
                                        label="Required", required=False
                                    ),
                                ),
                                (
                                    "default_value",
                                    wagtail.blocks.BooleanBlock(required=False),
                                ),
                            ],
                            group="Fields",
                        ),
                    ),
                    (
                        "radios",
                        wagtail.blocks.StructBlock(
                            [
                                (
                                    "field_label",
                                    wagtail.blocks.CharBlock(label="Label"),
                                ),
                                (
                                    "help_text",
                                    wagtail.blocks.RichTextBlock(
                                        label="Help text", required=False
                                    ),
                                ),
                                (
                                    "required",
                                    wagtail.blocks.BooleanBlock(
                                        label="Required", required=False
                                    ),
                                ),
                                (
                                    "choices",
                                    wagtail.blocks.ListBlock(
                                        wagtail.blocks.CharBlock(label="Choice")
                                    ),
                                ),
                            ],
                            group="Fields",
                        ),
                    ),
                    (
                        "dropdown",
                        wagtail.blocks.StructBlock(
                            [
                                (
                                    "field_label",
                                    wagtail.blocks.CharBlock(label="Label"),
                                ),
                                (
                                    "help_text",
                                    wagtail.blocks.RichTextBlock(
                                        label="Help text", required=False
                                    ),
                                ),
                                (
                                    "required",
                                    wagtail.blocks.BooleanBlock(
                                        label="Required", required=False
                                    ),
                                ),
                                (
                                    "choices",
                                    wagtail.blocks.ListBlock(
                                        wagtail.blocks.CharBlock(label="Choice")
                                    ),
                                ),
                            ],
                            group="Fields",
                        ),
                    ),
                    (
                        "checkboxes",
                        wagtail.blocks.StructBlock(
                            [
                                (
                                    "field_label",
                                    wagtail.blocks.CharBlock(label="Label"),
                                ),
                                (
                                    "help_text",
                                    wagtail.blocks.RichTextBlock(
                                        label="Help text", required=False
                                    ),
                                ),
                                (
                                    "required",
                                    wagtail.blocks.BooleanBlock(
                                        label="Required", required=False
                                    ),
                                ),
                                (
                                    "checkboxes",
                                    wagtail.blocks.ListBlock(
                                        wagtail.blocks.CharBlock(label="Checkbox")
                                    ),
                                ),
                            ],
                            group="Fields",
                        ),
                    ),
                    (
                        "date",
                        wagtail.blocks.StructBlock(
                            [
                                (
                                    "field_label",
                                    wagtail.blocks.CharBlock(label="Label"),
                                ),
                                (
                                    "help_text",
                                    wagtail.blocks.RichTextBlock(
                                        label="Help text", required=False
                                    ),
                                ),
                                (
                                    "required",
                                    wagtail.blocks.BooleanBlock(
                                        label="Required", required=False
                                    ),
                                ),
                                (
                                    "default_value",
                                    wagtail.blocks.DateBlock(required=False),
                                ),
                            ],
                            group="Fields",
                        ),
                    ),
                    (
                        "time",
                        wagtail.blocks.StructBlock(
                            [
                                (
                                    "field_label",
                                    wagtail.blocks.CharBlock(label="Label"),
                                ),
                                (
                                    "help_text",
                                    wagtail.blocks.RichTextBlock(
                                        label="Help text", required=False
                                    ),
                                ),
                                (
                                    "required",
                                    wagtail.blocks.BooleanBlock(
                                        label="Required", required=False
                                    ),
                                ),
                                (
                                    "default_value",
                                    wagtail.blocks.TimeBlock(required=False),
                                ),
                            ],
                            group="Fields",
                        ),
                    ),
                    (
                        "datetime",
                        wagtail.blocks.StructBlock(
                            [
                                (
                                    "field_label",
                                    wagtail.blocks.CharBlock(label="Label"),
                                ),
                                (
                                    "help_text",
                                    wagtail.blocks.RichTextBlock(
                                        label="Help text", required=False
                                    ),
                                ),
                                (
                                    "required",
                                    wagtail.blocks.BooleanBlock(
                                        label="Required", required=False
                                    ),
                                ),
                                (
                                    "default_value",
                                    wagtail.blocks.DateTimeBlock(required=False),
                                ),
                            ],
                            group="Fields",
                        ),
                    ),
                    (
                        "image",
                        wagtail.blocks.StructBlock(
                            [
                                (
                                    "field_label",
                                    wagtail.blocks.CharBlock(label="Label"),
                                ),
                                (
                                    "help_text",
                                    wagtail.blocks.RichTextBlock(
                                        label="Help text", required=False
                                    ),
                                ),
                                (
                                    "required",
                                    wagtail.blocks.BooleanBlock(
                                        label="Required", required=False
                                    ),
                                ),
                            ],
                            group="Fields",
                        ),
                    ),
                    (
                        "file",
                        wagtail.blocks.StructBlock(
                            [
                                (
                                    "field_label",
                                    wagtail.blocks.CharBlock(label="Label"),
                                ),
                                (
                                    "help_text",
                                    wagtail.blocks.RichTextBlock(
                                        label="Help text", required=False
                                    ),
                                ),
                                (
                                    "required",
                                    wagtail.blocks.BooleanBlock(
                                        label="Required", required=False
                                    ),
                                ),
                            ],
                            group="Fields",
                        ),
                    ),
                    (
                        "multi_file",
                        wagtail.blocks.StructBlock(
                            [
                                (
                                    "field_label",
                                    wagtail.blocks.CharBlock(label="Label"),
                                ),
                                (
                                    "help_text",
                                    wagtail.blocks.RichTextBlock(
                                        label="Help text", required=False
                                    ),
                                ),
                                (
                                    "required",
                                    wagtail.blocks.BooleanBlock(
                                        label="Required", required=False
                                    ),
                                ),
                            ],
                            group="Fields",
                        ),
                    ),
                    (
                        "group_toggle",
                        wagtail.blocks.StructBlock(
                            [
                                (
                                    "field_label",
                                    wagtail.blocks.CharBlock(label="Label"),
                                ),
                                (
                                    "help_text",
                                    wagtail.blocks.RichTextBlock(
                                        label="Help text", required=False
                                    ),
                                ),
                                (
                                    "required",
                                    wagtail.blocks.BooleanBlock(
                                        default=True, label="Required", required=False
                                    ),
                                ),
                                (
                                    "choices",
                                    wagtail.blocks.ListBlock(
                                        wagtail.blocks.CharBlock(label="Choice"),
                                        help_text="Please create only two choices for toggle. First choice will revel the group and the second hide it. Additional choices will be ignored.",
                                    ),
                                ),
                            ],
                            group="Custom",
                        ),
                    ),
                    (
                        "group_toggle_end",
                        hypha.apply.stream_forms.blocks.GroupToggleEndBlock(
                            group="Custom"
                        ),
                    ),
                    (
                        "rich_text",
                        wagtail.blocks.StructBlock(
                            [
                                (
                                    "field_label",
                                    wagtail.blocks.CharBlock(label="Label"),
                                ),
                                (
                                    "help_text",
                                    wagtail.blocks.RichTextBlock(
                                        label="Help text", required=False
                                    ),
                                ),
                                (
                                    "required",
                                    wagtail.blocks.BooleanBlock(
                                        label="Required", required=False
                                    ),
                                ),
                                (
                                    "default_value",
                                    wagtail.blocks.TextBlock(
                                        label="Default value", required=False
                                    ),
                                ),
                                (
                                    "word_limit",
                                    wagtail.blocks.IntegerBlock(
                                        default=1000, label="Word limit"
                                    ),
                                ),
                            ],
                            group="Fields",
                        ),
                    ),
                    (
                        "markdown_text",
                        wagtail.blocks.StructBlock(
                            [
                                (
                                    "field_label",
                                    wagtail.blocks.CharBlock(label="Label"),
                                ),
                                (
                                    "help_text",
                                    wagtail.blocks.RichTextBlock(
                                        label="Help text", required=False
                                    ),
                                ),
                                (
                                    "required",
                                    wagtail.blocks.BooleanBlock(
                                        label="Required", required=False
                                    ),
                                ),
                                (
                                    "default_value",
                                    wagtail.blocks.TextBlock(
                                        label="Default value", required=False
                                    ),
                                ),
                                (
                                    "word_limit",
                                    wagtail.blocks.IntegerBlock(
                                        default=1000, label="Word limit"
                                    ),
                                ),
                            ],
                            group="Fields",
                        ),
                    ),
                ],
                default=dict,
                use_json_field=True,
            ),
            preserve_default=False,
        ),
    ]
