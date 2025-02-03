# Generated by Django 4.2.18 on 2025-01-31 20:34

from django.db import migrations
import wagtail.blocks
import wagtail.blocks.static_block
import wagtail.fields


def merge_help_text_link(apps, schema_editor):
    DeterminationForm = apps.get_model("determinations", "DeterminationForm")
    for determinationform in DeterminationForm.objects.all():
        for id, struct_child in enumerate(determinationform.form_fields):
            struct_value = struct_child.value
            if (
                struct_value["help_text"]
                and struct_value["help_link"]
                and struct_value["help_link"] != ""
            ):
                determinationform.form_fields[id].value["help_text"] = (
                    "%s [See help guide for more information.](%s)"
                    % (
                        determinationform.form_fields[id].value["help_text"],
                        determinationform.form_fields[id].value["help_link"],
                    )
                )
        determinationform.save()


class Migration(migrations.Migration):
    dependencies = [
        ("determinations", "0017_remove_drupal_id_field"),
    ]

    operations = [
        migrations.RunPython(merge_help_text_link),
        migrations.AlterField(
            model_name="determination",
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
                        "text_markup",
                        wagtail.blocks.RichTextBlock(group="Fields", label="Paragraph"),
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
                        "determination",
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
                        "message",
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
                        "send_notice",
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
                                    "default_value",
                                    wagtail.blocks.BooleanBlock(
                                        default=True, required=False
                                    ),
                                ),
                                ("info", wagtail.blocks.static_block.StaticBlock()),
                            ],
                            group=" Required",
                        ),
                    ),
                ],
                default=[],
                use_json_field=True,
            ),
        ),
        migrations.AlterField(
            model_name="determinationform",
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
                        "text_markup",
                        wagtail.blocks.RichTextBlock(group="Fields", label="Paragraph"),
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
                        "determination",
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
                        "message",
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
                        "send_notice",
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
                                    "default_value",
                                    wagtail.blocks.BooleanBlock(
                                        default=True, required=False
                                    ),
                                ),
                                ("info", wagtail.blocks.static_block.StaticBlock()),
                            ],
                            group=" Required",
                        ),
                    ),
                ],
                default=[],
                use_json_field=True,
            ),
        ),
    ]
