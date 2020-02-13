from django.db import models
from wagtail.core.models import Page
from wagtail.admin.edit_handlers import FieldPanel, MultiFieldPanel, PageChooserPanel
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.documents.edit_handlers import DocumentChooserPanel


# Create your models here.
class ResetNetworkAboutPage(Page):
    class Meta:
        verbose_name = "Reset Network About Page"

    parent_page_types = ['reset_network_home.ResetNetworkHomePage']
    subpage_types = []

    # Content elements
    content_heading = models.CharField(verbose_name='Heading', max_length=255, blank=False)
    content_heading_gif_desktop = models.ForeignKey('wagtaildocs.Document', verbose_name='Heading image desktop', null=True, blank=True,
                                                    related_name='+', on_delete=models.SET_NULL)
    content_heading_gif_mobile = models.ForeignKey('wagtaildocs.Document', verbose_name='Heading image mobile', null=True, blank=True,
                                                   related_name='+', on_delete=models.SET_NULL)
    content_text = models.TextField(blank=True, verbose_name='Text')

    # Section 1 elements
    section_1_heading = models.CharField(verbose_name='Heading', max_length=255, blank=True)
    section_1_text = models.TextField(verbose_name='Text', blank=True)
    section_1_image = models.ForeignKey('images.CustomImage', verbose_name='Image', null=True, blank=True,
                                        related_name='+', on_delete=models.SET_NULL)

    # Section 2 elements
    section_2_heading = models.CharField(verbose_name='Heading', max_length=255, blank=True)
    section_2_text = models.TextField(verbose_name='Text', blank=True)
    section_2_image = models.ForeignKey('images.CustomImage', verbose_name='Image', null=True, blank=True,
                                        related_name='+', on_delete=models.SET_NULL)

    # Section 3 elements
    section_3_heading = models.CharField(verbose_name='Heading', max_length=255, blank=True)
    section_3_text = models.TextField(verbose_name='Text', blank=True)
    section_3_image = models.ForeignKey('images.CustomImage', verbose_name='Image', null=True, blank=True,
                                        related_name='+', on_delete=models.SET_NULL)

    # Section 4 elements
    section_4_heading = models.CharField(verbose_name='Heading', max_length=255, blank=True)
    section_4_text = models.TextField(verbose_name='Text', blank=True)
    section_4_image = models.ForeignKey('images.CustomImage', verbose_name='Image', null=True, blank=True,
                                        related_name='+', on_delete=models.SET_NULL)

    # Section 5 elements
    section_5_heading = models.CharField(verbose_name='Heading', max_length=255, blank=True)
    section_5_text = models.TextField(verbose_name='Text', blank=True)
    section_5_image = models.ForeignKey('images.CustomImage', verbose_name='Image', null=True, blank=True,
                                        related_name='+', on_delete=models.SET_NULL)
    section_5_link = models.ForeignKey('wagtailcore.Page', verbose_name='Link', null=True, blank=True, related_name='+',
                                       on_delete=models.PROTECT)
    section_5_link_text = models.CharField(verbose_name='Link text', max_length=255, blank=True)

    # Section 6 elements
    section_6_heading = models.CharField(verbose_name='Heading', max_length=255, blank=True)
    section_6_text = models.TextField(verbose_name='Text', blank=True)
    section_6_image = models.ForeignKey('images.CustomImage', verbose_name='Image', null=True, blank=True,
                                        related_name='+', on_delete=models.SET_NULL)

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('content_heading'),
            DocumentChooserPanel('content_heading_gif_desktop'),
            DocumentChooserPanel('content_heading_gif_mobile'),
            FieldPanel('content_text'),
        ], heading='Content'),
        MultiFieldPanel([
            FieldPanel('section_1_heading'),
            FieldPanel('section_1_text'),
            ImageChooserPanel('section_1_image'),
        ], heading='Content - Section 1'),
        MultiFieldPanel([
            FieldPanel('section_2_heading'),
            FieldPanel('section_2_text'),
            ImageChooserPanel('section_2_image'),
        ], heading='Content - Section 2'),
        MultiFieldPanel([
            FieldPanel('section_3_heading'),
            FieldPanel('section_3_text'),
            ImageChooserPanel('section_3_image'),
        ], heading='Content - Section 3'),
        MultiFieldPanel([
            FieldPanel('section_4_heading'),
            FieldPanel('section_4_text'),
            ImageChooserPanel('section_4_image'),
        ], heading='Content - Section 4'),
        MultiFieldPanel([
            FieldPanel('section_5_heading'),
            FieldPanel('section_5_text'),
            ImageChooserPanel('section_5_image'),
            PageChooserPanel('section_5_link'),
            FieldPanel('section_5_link_text')
        ], heading='Content - Section 5'),
        MultiFieldPanel([
            FieldPanel('section_6_heading'),
            FieldPanel('section_6_text'),
            ImageChooserPanel('section_6_image'),

        ], heading='Content - Section 6'),
    ]
