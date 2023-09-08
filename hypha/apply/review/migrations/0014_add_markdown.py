# Generated by Django 2.0.9 on 2018-11-14 12:29

from django.db import migrations
import wagtail.blocks
import wagtail.blocks.static_block
import wagtail.fields


class Migration(migrations.Migration):
    dependencies = [
        ("review", "0013_rename_fields"),
    ]

    operations = [
        migrations.AlterField(
            model_name="review",
            name="form_fields",
            field=wagtail.fields.StreamField(
                [
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
                                    wagtail.blocks.TextBlock(
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
                                    wagtail.blocks.TextBlock(
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
                            ],
                            group="Fields",
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
                                    wagtail.blocks.TextBlock(
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
                        "text",
                        wagtail.blocks.StructBlock(
                            [
                                (
                                    "field_label",
                                    wagtail.blocks.CharBlock(label="Label"),
                                ),
                                (
                                    "help_text",
                                    wagtail.blocks.TextBlock(
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
                            ],
                            group="Fields",
                        ),
                    ),
                    (
                        "text_markup",
                        wagtail.blocks.RichTextBlock(group="Fields", label="Paragraph"),
                    ),
                    (
                        "score",
                        wagtail.blocks.StructBlock(
                            [
                                (
                                    "field_label",
                                    wagtail.blocks.CharBlock(label="Label"),
                                ),
                                (
                                    "help_text",
                                    wagtail.blocks.TextBlock(
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
                        "checkbox",
                        wagtail.blocks.StructBlock(
                            [
                                (
                                    "field_label",
                                    wagtail.blocks.CharBlock(label="Label"),
                                ),
                                (
                                    "help_text",
                                    wagtail.blocks.TextBlock(
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
                        "dropdown",
                        wagtail.blocks.StructBlock(
                            [
                                (
                                    "field_label",
                                    wagtail.blocks.CharBlock(label="Label"),
                                ),
                                (
                                    "help_text",
                                    wagtail.blocks.TextBlock(
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
                        "recommendation",
                        wagtail.blocks.StructBlock(
                            [
                                (
                                    "field_label",
                                    wagtail.blocks.CharBlock(label="Label"),
                                ),
                                (
                                    "help_text",
                                    wagtail.blocks.TextBlock(
                                        label="Help text", required=False
                                    ),
                                ),
                                ("info", wagtail.blocks.static_block.StaticBlock()),
                            ],
                            group=" Required",
                        ),
                    ),
                    (
                        "comments",
                        wagtail.blocks.StructBlock(
                            [
                                (
                                    "field_label",
                                    wagtail.blocks.CharBlock(label="Label"),
                                ),
                                (
                                    "help_text",
                                    wagtail.blocks.TextBlock(
                                        label="Help text", required=False
                                    ),
                                ),
                                ("info", wagtail.blocks.static_block.StaticBlock()),
                            ],
                            group=" Required",
                        ),
                    ),
                ]
            ),
        ),
        migrations.AlterField(
            model_name="reviewform",
            name="form_fields",
            field=wagtail.fields.StreamField(
                [
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
                                    wagtail.blocks.TextBlock(
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
                                    wagtail.blocks.TextBlock(
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
                            ],
                            group="Fields",
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
                                    wagtail.blocks.TextBlock(
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
                        "text",
                        wagtail.blocks.StructBlock(
                            [
                                (
                                    "field_label",
                                    wagtail.blocks.CharBlock(label="Label"),
                                ),
                                (
                                    "help_text",
                                    wagtail.blocks.TextBlock(
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
                            ],
                            group="Fields",
                        ),
                    ),
                    (
                        "text_markup",
                        wagtail.blocks.RichTextBlock(group="Fields", label="Paragraph"),
                    ),
                    (
                        "score",
                        wagtail.blocks.StructBlock(
                            [
                                (
                                    "field_label",
                                    wagtail.blocks.CharBlock(label="Label"),
                                ),
                                (
                                    "help_text",
                                    wagtail.blocks.TextBlock(
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
                        "checkbox",
                        wagtail.blocks.StructBlock(
                            [
                                (
                                    "field_label",
                                    wagtail.blocks.CharBlock(label="Label"),
                                ),
                                (
                                    "help_text",
                                    wagtail.blocks.TextBlock(
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
                        "dropdown",
                        wagtail.blocks.StructBlock(
                            [
                                (
                                    "field_label",
                                    wagtail.blocks.CharBlock(label="Label"),
                                ),
                                (
                                    "help_text",
                                    wagtail.blocks.TextBlock(
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
                        "recommendation",
                        wagtail.blocks.StructBlock(
                            [
                                (
                                    "field_label",
                                    wagtail.blocks.CharBlock(label="Label"),
                                ),
                                (
                                    "help_text",
                                    wagtail.blocks.TextBlock(
                                        label="Help text", required=False
                                    ),
                                ),
                                ("info", wagtail.blocks.static_block.StaticBlock()),
                            ],
                            group=" Required",
                        ),
                    ),
                    (
                        "comments",
                        wagtail.blocks.StructBlock(
                            [
                                (
                                    "field_label",
                                    wagtail.blocks.CharBlock(label="Label"),
                                ),
                                (
                                    "help_text",
                                    wagtail.blocks.TextBlock(
                                        label="Help text", required=False
                                    ),
                                ),
                                ("info", wagtail.blocks.static_block.StaticBlock()),
                            ],
                            group=" Required",
                        ),
                    ),
                ]
            ),
        ),
    ]
