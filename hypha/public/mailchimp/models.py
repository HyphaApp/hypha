from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel
from wagtail.contrib.settings.models import BaseSetting

from hypha.core.wagtail.admin import register_public_site_setting


@register_public_site_setting
class NewsletterSettings(BaseSetting):
    class Meta:
        verbose_name = 'newsletter settings'

    newsletter_title = models.CharField(
        "Newsletter title",
        max_length=255,
        default='Get the latest internet freedom news',
        help_text=_('The title of the newsletter signup form.'),
    )

    panels = [
        FieldPanel('newsletter_title'),
    ]
