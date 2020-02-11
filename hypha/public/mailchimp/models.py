from django.db import models

from wagtail.admin.edit_handlers import FieldPanel
from wagtail.contrib.settings.models import BaseSetting, register_setting


@register_setting
class NewsletterSettings(BaseSetting):
    class Meta:
        verbose_name = 'newsletter settings'

    newsletter_title = models.CharField(
        "Newsletter title",
        max_length=255,
        default='Get the latest internet freedom news',
        help_text='The title of the newsletter signup form.',
    )

    panels = [
        FieldPanel('newsletter_title'),
    ]
