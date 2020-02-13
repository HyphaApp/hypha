from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.core.models import Page, Orderable
from wagtail.core.fields import RichTextField
from wagtail.admin.edit_handlers import FieldPanel, MultiFieldPanel, InlinePanel
from modelcluster.fields import ParentalKey
from django.db import models


class ResetNetworkWorkPagePillar(Orderable):

    page = ParentalKey('reset_network_work.ResetNetworkWorkPage', related_name='reset_network_work_pillar',
                       on_delete=models.CASCADE)

    heading = models.CharField(verbose_name='Heading', max_length=255, blank=False)
    text = models.TextField(verbose_name='Text', blank=True)
    image = models.ForeignKey('images.CustomImage', null=True, blank=True, related_name='+', on_delete=models.SET_NULL)

    panels = [
        FieldPanel('heading'),
        FieldPanel('text'),
        ImageChooserPanel('image'),
    ]


class ResetNetworkWorkPageRegion(Orderable):

    page = ParentalKey('reset_network_work.ResetNetworkWorkPage', related_name='reset_network_work_region',
                       on_delete=models.CASCADE)

    heading = models.CharField(verbose_name='Heading', max_length=255, blank=False)
    text = RichTextField(verbose_name='Text', blank=True)

    panels = [
        FieldPanel('heading'),
        FieldPanel('text'),
    ]


class ResetNetworkWorkPage(Page):

    class Meta:
        verbose_name = "Reset Network Work Page"

    parent_page_types = ['reset_network_home.ResetNetworkHomePage']
    subpage_types = []

    content_heading = models.CharField(verbose_name='Heading', max_length=255, blank=False)
    content_text = models.TextField(verbose_name='Text', blank=True)

    region_heading = models.CharField(verbose_name='Heading', max_length=255, blank=False)

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('content_heading'),
            FieldPanel('content_text'),
        ], heading='Content'),
        MultiFieldPanel([
            InlinePanel('reset_network_work_pillar', label='Pillar', heading='Pillar')
        ], heading='content - Pillars'),
        MultiFieldPanel([
            FieldPanel('region_heading'),
            InlinePanel('reset_network_work_region', label='Region', heading='Region')
        ], heading='Content - Regions'),
    ]
