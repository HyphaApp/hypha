# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2018-01-11 14:47
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import hypha.public.funds.blocks
import wagtail.blocks
import wagtail.fields
import wagtail.documents.blocks
import wagtail.embeds.blocks
import wagtail.images.blocks
import wagtail.snippets.blocks


class Migration(migrations.Migration):
    dependencies = [
        ("images", "0001_initial"),
        ("wagtailcore", "0040_page_draft_title"),
        ("public_funds", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="LabIndex",
            fields=[
                (
                    "page_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="wagtailcore.Page",
                    ),
                ),
                ("social_text", models.CharField(blank=True, max_length=255)),
                (
                    "listing_title",
                    models.CharField(
                        blank=True,
                        help_text="Override the page title used when this page appears in listings",
                        max_length=255,
                    ),
                ),
                (
                    "listing_summary",
                    models.CharField(
                        blank=True,
                        help_text="The text summary used when this page appears in listings. It's also used as the description for search engines if the 'Search description' field above is not defined.",
                        max_length=255,
                    ),
                ),
                ("introduction", models.TextField(blank=True)),
                (
                    "header_image",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="images.CustomImage",
                    ),
                ),
                (
                    "listing_image",
                    models.ForeignKey(
                        blank=True,
                        help_text="Choose the image you wish to be displayed when this page appears in listings",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="images.CustomImage",
                    ),
                ),
                (
                    "social_image",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="images.CustomImage",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("wagtailcore.page", models.Model),
        ),
        migrations.CreateModel(
            name="LabPage",
            fields=[
                (
                    "page_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="wagtailcore.Page",
                    ),
                ),
                ("social_text", models.CharField(blank=True, max_length=255)),
                (
                    "listing_title",
                    models.CharField(
                        blank=True,
                        help_text="Override the page title used when this page appears in listings",
                        max_length=255,
                    ),
                ),
                (
                    "listing_summary",
                    models.CharField(
                        blank=True,
                        help_text="The text summary used when this page appears in listings. It's also used as the description for search engines if the 'Search description' field above is not defined.",
                        max_length=255,
                    ),
                ),
                ("introduction", models.TextField(blank=True)),
                ("lab_link", models.URLField(blank=True, verbose_name="External link")),
                (
                    "link_text",
                    models.CharField(
                        help_text="Text to display on the button", max_length=255
                    ),
                ),
                (
                    "body",
                    wagtail.fields.StreamField(
                        (
                            (
                                "heading",
                                wagtail.blocks.CharBlock(
                                    classname="full title", icon="title"
                                ),
                            ),
                            ("paragraph", wagtail.blocks.RichTextBlock()),
                            (
                                "image",
                                wagtail.blocks.StructBlock(
                                    (
                                        (
                                            "image",
                                            wagtail.images.blocks.ImageChooserBlock(),
                                        ),
                                        (
                                            "caption",
                                            wagtail.blocks.CharBlock(required=False),
                                        ),
                                    )
                                ),
                            ),
                            (
                                "quote",
                                wagtail.blocks.StructBlock(
                                    (
                                        (
                                            "quote",
                                            wagtail.blocks.CharBlock(classname="title"),
                                        ),
                                        (
                                            "attribution",
                                            wagtail.blocks.CharBlock(required=False),
                                        ),
                                        (
                                            "job_title",
                                            wagtail.blocks.CharBlock(required=False),
                                        ),
                                    )
                                ),
                            ),
                            ("embed", wagtail.embeds.blocks.EmbedBlock()),
                            (
                                "call_to_action",
                                wagtail.snippets.blocks.SnippetChooserBlock(
                                    "utils.CallToActionSnippet",
                                    template="blocks/call_to_action_block.html",
                                ),
                            ),
                            (
                                "document",
                                wagtail.blocks.StructBlock(
                                    (
                                        (
                                            "document",
                                            wagtail.documents.blocks.DocumentChooserBlock(),
                                        ),
                                        (
                                            "title",
                                            wagtail.blocks.CharBlock(required=False),
                                        ),
                                    )
                                ),
                            ),
                            (
                                "reviewer_list",
                                hypha.public.funds.blocks.ReviewersBlock(),
                            ),
                        )
                    ),
                ),
                (
                    "header_image",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="images.CustomImage",
                    ),
                ),
                (
                    "lab_type",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="lab_public",
                        to="wagtailcore.Page",
                    ),
                ),
                (
                    "listing_image",
                    models.ForeignKey(
                        blank=True,
                        help_text="Choose the image you wish to be displayed when this page appears in listings",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="images.CustomImage",
                    ),
                ),
                (
                    "social_image",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="images.CustomImage",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("wagtailcore.page", models.Model),
        ),
    ]
