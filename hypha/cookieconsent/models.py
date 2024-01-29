from django.db import models
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.contrib.settings.models import BaseGenericSetting, register_setting
from wagtail.fields import RichTextField


@register_setting
class CookieConsentSettings(BaseGenericSetting):
    class Meta:
        verbose_name = "Cookie consent settings"

    cookieconsent_active = models.BooleanField(
        "Activate cookie consent feature",
        default=False,
    )

    cookieconsent_title = models.CharField(
        "cookie consent title",
        max_length=255,
        default="Your cookie settings",
    )

    cookieconsent_message = RichTextField(
        "cookie consent message",
        default='<p>This website deploys cookies for basic functionality and to keep it secure. These cookies are strictly necessary. Optional analysis cookies which provide us with statistical information about the use of the website may also be deployed, but only with your consent. Please review our <a href="/data-privacy-policy/">Privacy &amp; Data Policy</a> for more information.</p>',
    )

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("cookieconsent_active"),
                FieldPanel("cookieconsent_title"),
                FieldPanel("cookieconsent_message"),
            ],
            "cookie banner",
        ),
    ]
