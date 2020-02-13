from django.db import models
from modelcluster.fields import ParentalKey
from wagtail.core.models import Orderable, Page
import django.db.models.options as options
from wagtail.admin.edit_handlers import FieldPanel, InlinePanel, MultiFieldPanel, PageChooserPanel
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.documents.edit_handlers import DocumentChooserPanel

options.DEFAULT_NAMES = options.DEFAULT_NAMES + ('description',)


class ResetNetworkHomePageHeroImages(Orderable):
    page = ParentalKey('reset_network_home.ResetNetworkHomePage', related_name='reset_network_home_page_hero_images',
                       on_delete=models.CASCADE)

    image = models.ForeignKey('images.CustomImage', null=True, blank=False, related_name='+', on_delete=models.SET_NULL)

    panels = [
        ImageChooserPanel('image'),
    ]


class ResetNetworkHomePageOpenCalls(Orderable):
    open_calls_link = ParentalKey('reset_network_home.ResetNetworkHomePage',
                                  related_name='reset_network_home_page_open_calls', on_delete=models.CASCADE)

    open_call_link_page = models.ForeignKey('wagtailcore.Page', verbose_name='Open calls Page',
                                            help_text='The page to link to', null=True, blank=False, related_name='+',
                                            on_delete=models.SET_NULL)

    panels = [PageChooserPanel('open_call_link_page', page_type='reset_network_open_calls.ResetNetworkOpenCallPage')]


class ResetNetworkHomePageFeatured(Orderable):
    page = ParentalKey('reset_network_home.ResetNetworkHomePage', related_name='reset_network_home_page_featured',
                       on_delete=models.CASCADE)

    heading = models.CharField(verbose_name='Heading', max_length=255, blank=False)
    text = models.TextField(verbose_name='Text', blank=True)
    image = models.ForeignKey('images.CustomImage', null=True, blank=True, related_name='+', on_delete=models.SET_NULL)
    link = models.URLField(verbose_name='Link', blank=False)

    panels = [
        FieldPanel('heading'),
        FieldPanel('text'),
        ImageChooserPanel('image'),
        FieldPanel('link'),
    ]


class ResetNetworkHomePage(Page):
    class Meta:
        verbose_name = "Reset Network Home Page"

    parent_page_types = ['wagtailcore.Page']
    subpage_types = [
        'reset_network_about.ResetNetworkAboutPage',
        'reset_network_open_calls.ResetNetworkOpenCallsPage',
        'reset_network_people.ResetNetworkPeoplePage',
        'reset_network_resources.ResetNetworkResourcesPage',
        'reset_network_work.ResetNetworkWorkPage',
        'reset_network_basic_page.ResetNetworkBasicPage',
        'reset_network_contact_us.ResetNetworkContactUsPage',
    ]

    # Content elements
    content_heading = models.CharField(verbose_name='Heading', max_length=255, blank=False)
    content_heading_gif_desktop = models.ForeignKey('wagtaildocs.Document', verbose_name='Heading image desktop', null=True, blank=True,
                                                    related_name='+', on_delete=models.SET_NULL)
    content_heading_gif_mobile = models.ForeignKey('wagtaildocs.Document', verbose_name='Heading image mobile', null=True, blank=True,
                                                   related_name='+', on_delete=models.SET_NULL)
    content_text = models.TextField(verbose_name='Text', blank=True)
    content_link = models.ForeignKey('wagtailcore.Page', verbose_name='Link', null=True, blank=True, related_name='+',
                                     on_delete=models.PROTECT)
    content_link_text = models.CharField(verbose_name='Link text', max_length=255, blank=True)

    # Section 1 elements
    section_1_heading = models.CharField(verbose_name='Heading', max_length=255, blank=True)
    section_1_text = models.TextField(verbose_name='Text', blank=True)
    section_1_link = models.ForeignKey('wagtailcore.Page', verbose_name='Link', null=True, blank=True, related_name='+',
                                       on_delete=models.PROTECT)
    section_1_link_text = models.CharField(verbose_name='Link text', max_length=255, blank=True)
    section_1_image = models.ForeignKey('images.CustomImage', null=True, blank=True, related_name='+',
                                        on_delete=models.SET_NULL)

    # Section 2 (open calls) elements
    section_2_heading = models.CharField(verbose_name='Heading', max_length=255, blank=True)
    section_2_text = models.TextField(verbose_name='Text', blank=True)
    section_2_link = models.ForeignKey('wagtailcore.Page', verbose_name='Link', null=True, blank=True, related_name='+',
                                       on_delete=models.PROTECT)
    section_2_link_text = models.CharField(verbose_name='Link text', max_length=255, blank=True)
    section_2_image = models.ForeignKey('images.CustomImage', null=True, blank=True, related_name='+',
                                        on_delete=models.SET_NULL)

    # Section 3 (resources) elements
    section_3_heading = models.CharField(verbose_name='Heading', max_length=255, blank=True)
    section_3_link = models.ForeignKey('wagtailcore.Page', verbose_name='Link', null=True, blank=True, related_name='+',
                                       on_delete=models.PROTECT)
    section_3_link_text = models.CharField(verbose_name='Link text', max_length=255, blank=True)

    content_panels = Page.content_panels + [
        InlinePanel('reset_network_home_page_hero_images', label='Hero Image', heading='Hero Images'),
        MultiFieldPanel([
            FieldPanel('content_heading'),
            DocumentChooserPanel('content_heading_gif_desktop'),
            DocumentChooserPanel('content_heading_gif_mobile'),
            FieldPanel('content_text'),
            PageChooserPanel('content_link'),
            FieldPanel('content_link_text'),
        ], heading='Content'),
        MultiFieldPanel([
            FieldPanel('section_1_heading'),
            FieldPanel('section_1_text'),
            PageChooserPanel('section_1_link'),
            FieldPanel('section_1_link_text'),
            ImageChooserPanel('section_1_image'),
        ], heading='Content - Section 1'),
        MultiFieldPanel([
            FieldPanel('section_2_heading'),
            FieldPanel('section_2_text'),
            PageChooserPanel('section_2_link'),
            FieldPanel('section_2_link_text'),
            ImageChooserPanel('section_2_image'),
            InlinePanel('reset_network_home_page_open_calls', label='Open Call Link', heading='Open Call Links'),
        ], heading='Content - Section 2 (Open Calls)'),
        MultiFieldPanel([
            FieldPanel('section_3_heading'),
            PageChooserPanel('section_3_link'),
            FieldPanel('section_3_link_text'),
            InlinePanel('reset_network_home_page_featured', label='Featured Card', heading='Featured'),
        ], heading='Content - Section 3 (Resources)'),
    ]
