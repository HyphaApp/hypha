# Generated by Django 4.2.11 on 2024-03-11 08:01

from django.db import migrations, models
import django.db.models.deletion
import wagtail.fields


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("images", "0006_alter_rendition_file"),
        ("core", "0002_auto_20240215_remove_mailhimp"),
    ]

    operations = [
        migrations.CreateModel(
            name="SystemSettings",
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
                    "site_logo_link",
                    models.URLField(
                        blank=True,
                        default="",
                        help_text='Link for the site logo, e.g. "https://www.example.org/". If not set, defaults to page with slug set to "home".',
                    ),
                ),
                (
                    "nav_content",
                    models.TextField(
                        blank=True,
                        help_text="This will overwrite the default front page navigation bar, html tags is allowed.",
                        verbose_name="Front page navigation content",
                    ),
                ),
                (
                    "footer_content",
                    models.TextField(
                        blank=True,
                        default="<p>Configure this text in Wagtail admin -> Settings -> System settings.</p>",
                        help_text="This will be added to the footer, html tags is allowed.",
                        verbose_name="Footer content",
                    ),
                ),
                (
                    "title_404",
                    models.CharField(
                        default="Page not found", max_length=255, verbose_name="Title"
                    ),
                ),
                (
                    "body_404",
                    wagtail.fields.RichTextField(
                        default="<p>You may be trying to find a page that doesn&rsquo;t exist or has been moved.</p>",
                        verbose_name="Text",
                    ),
                ),
                (
                    "title_403",
                    models.CharField(
                        default="Permission Denied",
                        max_length=255,
                        verbose_name="Title",
                    ),
                ),
                (
                    "body_403",
                    wagtail.fields.RichTextField(
                        default="<p>You might not have access to the requested resource.</p>",
                        verbose_name="Text",
                    ),
                ),
                (
                    "site_logo_default",
                    models.ForeignKey(
                        blank=True,
                        help_text="Default site logo",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="images.customimage",
                    ),
                ),
                (
                    "site_logo_mobile",
                    models.ForeignKey(
                        blank=True,
                        help_text="Mobil site logo (if not set default will be used)",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="images.customimage",
                    ),
                ),
            ],
            options={
                "verbose_name": "System settings",
                "db_table": "system_settings",
            },
        ),
    ]
