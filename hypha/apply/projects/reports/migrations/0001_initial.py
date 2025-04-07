# Generated by Django 4.2.20 on 2025-03-26 07:02

from django.conf import settings
import django.core.files.storage
from django.db import migrations, models
import django.db.models.deletion
import hypha.apply.funds.models.mixins
import hypha.apply.projects.reports.models
import hypha.apply.stream_forms.blocks
import hypha.apply.stream_forms.files
import hypha.apply.stream_forms.models
import wagtail.blocks
import wagtail.fields


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("application_projects", "0098_move_project_comments_to_application"),
    ]

    state_operations = [
        migrations.CreateModel(
            name="Report",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("skipped", models.BooleanField(default=False)),
                ("end_date", models.DateField()),
                (
                    "form_fields",
                    wagtail.fields.StreamField(
                        [
                            (
                                "text_markup",
                                wagtail.blocks.RichTextBlock(
                                    group="Custom", label="Paragraph"
                                ),
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
                                                choices=[
                                                    ("email", "Email"),
                                                    ("url", "URL"),
                                                ],
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
                                                choices=[
                                                    ("email", "Email"),
                                                    ("url", "URL"),
                                                ],
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
                                                wagtail.blocks.CharBlock(
                                                    label="Checkbox"
                                                )
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
                                            wagtail.blocks.DateTimeBlock(
                                                required=False
                                            ),
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
                                                default=True,
                                                label="Required",
                                                required=False,
                                            ),
                                        ),
                                        (
                                            "choices",
                                            wagtail.blocks.ListBlock(
                                                wagtail.blocks.CharBlock(
                                                    label="Choice"
                                                ),
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
                        null=True,
                        use_json_field=True,
                    ),
                ),
                (
                    "form_data",
                    models.JSONField(
                        default=dict,
                        encoder=hypha.apply.stream_forms.files.StreamFieldDataEncoder,
                    ),
                ),
                ("submitted", models.DateTimeField(null=True)),
                ("notified", models.DateTimeField(null=True)),
            ],
            options={
                "db_table": "application_projects_report",
                "ordering": ("-end_date",),
            },
            bases=(
                hypha.apply.stream_forms.models.BaseStreamForm,
                hypha.apply.funds.models.mixins.AccessFormData,
                models.Model,
            ),
        ),
        migrations.CreateModel(
            name="ReportVersion",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("submitted", models.DateTimeField()),
                (
                    "form_data",
                    models.JSONField(
                        default=dict,
                        encoder=hypha.apply.stream_forms.files.StreamFieldDataEncoder,
                    ),
                ),
                ("draft", models.BooleanField()),
                (
                    "author",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="reports",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "report",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="versions",
                        to="project_reports.report",
                    ),
                ),
            ],
            options={
                "db_table": "application_projects_reportversion",
            },
            bases=(
                hypha.apply.stream_forms.models.BaseStreamForm,
                hypha.apply.funds.models.mixins.AccessFormData,
                models.Model,
            ),
        ),
        migrations.CreateModel(
            name="ReportPrivateFiles",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "document",
                    models.FileField(
                        storage=django.core.files.storage.FileSystemStorage(),
                        upload_to=hypha.apply.projects.reports.models.report_path,
                    ),
                ),
                (
                    "report",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="files",
                        to="project_reports.reportversion",
                    ),
                ),
            ],
            options={
                "db_table": "application_projects_reportprivatefiles",
            },
        ),
        migrations.CreateModel(
            name="ReportConfig",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("schedule_start", models.DateField(null=True)),
                ("occurrence", models.PositiveSmallIntegerField(default=1)),
                (
                    "frequency",
                    models.CharField(
                        choices=[
                            ("week", "Weeks"),
                            ("month", "Months"),
                            ("year", "Years"),
                        ],
                        default="month",
                        max_length=6,
                    ),
                ),
                ("disable_reporting", models.BooleanField(default=True)),
                ("does_not_repeat", models.BooleanField(default=False)),
                (
                    "project",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="report_config",
                        to="application_projects.project",
                    ),
                ),
            ],
            options={
                "db_table": "application_projects_reportconfig",
            },
        ),
        migrations.AddField(
            model_name="report",
            name="current",
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="live_for_report",
                to="project_reports.reportversion",
            ),
        ),
        migrations.AddField(
            model_name="report",
            name="draft",
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="draft_for_report",
                to="project_reports.reportversion",
            ),
        ),
        migrations.AddField(
            model_name="report",
            name="project",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="reports",
                to="application_projects.project",
            ),
        ),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(state_operations=state_operations)
    ]
