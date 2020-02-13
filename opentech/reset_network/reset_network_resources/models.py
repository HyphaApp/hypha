from django.db import models
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey
from taggit.models import TaggedItemBase
from wagtail.admin.edit_handlers import FieldPanel, MultiFieldPanel, InlinePanel
from wagtail.core.fields import RichTextField
from wagtail.core.models import Page, Orderable
from wagtail.documents.edit_handlers import DocumentChooserPanel
from wagtail.images.edit_handlers import ImageChooserPanel


class ResetNetworkResourcePageAsset(Orderable):

    page = ParentalKey('wagtailcore.Page', related_name='reset_network_resource_page_assets', on_delete=models.CASCADE)

    heading = models.CharField(verbose_name='Heading', max_length=255, blank=False)
    text = models.TextField(verbose_name='Text', blank=True)
    asset = models.ForeignKey('wagtaildocs.Document', null=True, blank=False, related_name='+', on_delete=models.SET_NULL)

    panels = [
        FieldPanel('heading'),
        FieldPanel('text'),
        DocumentChooserPanel('asset'),
    ]


class ResetNetworkResourcePageLink(Orderable):

    page = ParentalKey('wagtailcore.Page', related_name='reset_network_resource_page_links', on_delete=models.CASCADE)

    heading = models.CharField(verbose_name='Heading', max_length=255, blank=False)
    link = models.URLField(verbose_name='Link', blank=False)

    panels = [
        FieldPanel('heading'),
        FieldPanel('link'),
    ]


class ResetNetworkResourcePageCategory(TaggedItemBase):

    content_object = ParentalKey('ResetNetworkResourcePage', related_name='reset_network_resource_page_category', on_delete=models.CASCADE)


class ResetNetworkResourcesPage(Page):

    class Meta:
        verbose_name = "Reset Network Resources Page"

    parent_page_types = ['reset_network_home.ResetNetworkHomePage']
    subpage_types = ['reset_network_resources.ResetNetworkResourcePage']

    content_heading = models.CharField(verbose_name='Heading', max_length=255, blank=False)

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('content_heading'),
        ], 'Content')
    ]

    def get_context(self, request, *args, **kwargs):

        category = request.GET.get('category', None)

        categories = ResetNetworkResourcePage.categories.order_by('name').all()

        resources = ResetNetworkResourcePage.objects.live().public().order_by('id').all()
        if category:
            resources = resources.filter(categories__name=category)

        context = super().get_context(request, *args, **kwargs)
        context['category'] = category
        context['categories'] = categories
        context['resources'] = resources
        return context


class ResetNetworkResourcePage(Page):

    class Meta:
        verbose_name = "Reset Network Resource Page"

    parent_page_types = ['reset_network_resources.ResetNetworkResourcesPage']
    subpage_types = []

    content_heading = models.CharField(verbose_name='Heading', max_length=255, blank=False)
    content_image = models.ForeignKey('images.CustomImage', verbose_name='Image',
                                      null=True, blank=True, related_name='+',
                                      on_delete=models.SET_NULL)
    content_text = RichTextField(blank=True, verbose_name='Text')

    categories = ClusterTaggableManager(through=ResetNetworkResourcePageCategory, blank=True)

    content_assets_heading = models.CharField(verbose_name='Heading', max_length=255, blank=False)

    content_links_heading = models.CharField(verbose_name='Heading', max_length=255, blank=False)

    card_heading = models.CharField(max_length=100, blank=False)
    card_text = models.TextField(blank=True)
    card_image = models.ForeignKey('images.CustomImage', null=True, blank=True, related_name='+',
                                   on_delete=models.SET_NULL)

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('content_heading'),
            ImageChooserPanel('content_image'),
            FieldPanel('content_text'),
            FieldPanel('categories'),
        ], heading='Content'),
        MultiFieldPanel([
            FieldPanel('content_assets_heading'),
            InlinePanel('reset_network_resource_page_assets', label='Asset', heading='Assets'),
        ], 'Content - Assets'),
        MultiFieldPanel([
            FieldPanel('content_links_heading'),
            InlinePanel('reset_network_resource_page_links', label='Link', heading='Links'),
        ], 'Content - Links'),
        MultiFieldPanel([
            FieldPanel('card_heading'),
            FieldPanel('card_text'),
            ImageChooserPanel('card_image'),
        ], heading='Card Details'),
    ]
