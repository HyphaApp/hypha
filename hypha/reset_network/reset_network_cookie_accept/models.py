from django.db import models
from wagtail.admin.edit_handlers import MultiFieldPanel, FieldPanel
from wagtail.contrib.settings.models import BaseSetting, register_setting
from wagtail.core.fields import RichTextField


@register_setting(icon='cog')
class ResetNetworkCookieAccept(BaseSetting):

    class Meta:
        verbose_name = 'Reset Network Cookie Accept'

    content_heading = models.CharField(
        verbose_name='Title',
        max_length=255,
        blank=False
    )

    content_text = RichTextField(
        verbose_name='Text',
        blank=False
    )

    content_decline_text = models.CharField(
        verbose_name='Decline Button Label',
        max_length=255,
        blank=False
    )

    content_accept_text = models.CharField(
        verbose_name='Accept Button Label',
        max_length=255,
        blank=False
    )

    panels = [
        MultiFieldPanel([
            FieldPanel('content_heading'),
            FieldPanel('content_text'),
            FieldPanel('content_decline_text'),
            FieldPanel('content_accept_text'),
        ], heading='Content'),
    ]
