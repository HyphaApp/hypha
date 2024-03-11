from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import (
    FieldPanel,
    MultiFieldPanel,
)
from wagtail.contrib.settings.models import (
    BaseGenericSetting,
    register_setting,
)
from wagtail.fields import RichTextField


@register_setting
class SystemSettings(BaseGenericSetting):
    class Meta:
        verbose_name = "System settings"
        db_table = "system_settings"

    site_logo_default = models.ForeignKey(
        "images.CustomImage",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text=_("Default site logo"),
    )

    site_logo_mobile = models.ForeignKey(
        "images.CustomImage",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text=_("Mobil site logo (if not set default will be used)"),
    )

    site_logo_link = models.URLField(
        default="",
        blank=True,
        help_text=_(
            'Link for the site logo, e.g. "https://www.example.org/". If not set, defaults to page with slug set to "home".'
        ),
    )

    nav_content = models.TextField(
        "Front page navigation content",
        help_text=_(
            "This will overwrite the default front page navigation bar, html tags is allowed."
        ),
        blank=True,
    )

    footer_content = models.TextField(
        "Footer content",
        default="<p>Configure this text in Wagtail admin -> Settings -> System settings.</p>",
        help_text=_("This will be added to the footer, html tags is allowed."),
        blank=True,
    )

    title_404 = models.CharField(
        "Title",
        max_length=255,
        default="Page not found",
    )
    body_404 = RichTextField(
        "Text",
        default="<p>You may be trying to find a page that doesn&rsquo;t exist or has been moved.</p>",
    )

    title_403 = models.CharField(
        "Title",
        max_length=255,
        default="Permission Denied",
    )
    body_403 = RichTextField(
        "Text",
        default="<p>You might not have access to the requested resource.</p>",
    )

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("site_logo_default"),
                FieldPanel("site_logo_mobile"),
                FieldPanel("site_logo_link"),
            ],
            "Site logo",
        ),
        FieldPanel("nav_content"),
        FieldPanel("footer_content"),
        MultiFieldPanel(
            [
                FieldPanel("title_404"),
                FieldPanel("body_404"),
            ],
            "404 page",
        ),
        MultiFieldPanel(
            [
                FieldPanel("title_403"),
                FieldPanel("body_403"),
            ],
            "403 page",
        ),
    ]
