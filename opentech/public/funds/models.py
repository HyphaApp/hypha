from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import models

from modelcluster.fields import ParentalKey
from wagtail.wagtailadmin.edit_handlers import (
    FieldPanel,
    FieldRowPanel,
    InlinePanel,
    MultiFieldPanel,
    PageChooserPanel,
    StreamFieldPanel,
)
from wagtail.wagtailcore.fields import StreamField
from wagtail.wagtailimages.edit_handlers import ImageChooserPanel

from opentech.public.utils.models import (
    BasePage,
    RelatedPage,
)

from .blocks import FundBlock, LabBlock


class FundPageRelatedPage(RelatedPage):
    source_page = ParentalKey('FundPage', related_name='related_pages')


class FundPage(BasePage):
    subpage_types = []
    parent_page_types = ['FundIndex']

    introduction = models.TextField(blank=True)
    fund_type = models.ForeignKey(
        'wagtailcore.Page',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    body = StreamField(FundBlock())

    content_panels = BasePage.content_panels + [
        FieldPanel('introduction'),
        PageChooserPanel('fund_type', 'funds.FundType'),
        StreamFieldPanel('body'),
        InlinePanel('related_pages', label="Related pages"),
    ]

    @property
    def is_open(self):
        return bool(self.fund_type.specific.open_round)

    @property
    def deadline(self):
        return self.fund_type.specific.next_deadline()


class FundIndex(BasePage):
    subpage_types = ['FundPage']
    parent_page_types = ['home.HomePage']

    introduction = models.TextField(blank=True)

    content_panels = BasePage.content_panels + [
        FieldPanel('introduction')
    ]

    def get_context(self, request, *args, **kwargs):
        funds = FundPage.objects.live().public().descendant_of(self)

        # Pagination
        page = request.GET.get('page', 1)
        paginator = Paginator(funds, settings.DEFAULT_PER_PAGE)
        try:
            funds = paginator.page(page)
        except PageNotAnInteger:
            funds = paginator.page(1)
        except EmptyPage:
            funds = paginator.page(paginator.num_pages)

        context = super().get_context(request, *args, **kwargs)
        context.update(subpages=funds)
        return context


class LabPageRelatedPage(RelatedPage):
    source_page = ParentalKey('LabPage', related_name='related_pages')


class LabPage(BasePage):
    subpage_types = []
    parent_page_types = ['LabIndex']

    introduction = models.TextField(blank=True)
    icon = models.ForeignKey(
        'images.CustomImage',
        null=True,
        blank=True,
        related_name='+',
        on_delete=models.SET_NULL
    )
    lab_type = models.ForeignKey(
        'wagtailcore.Page',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    lab_link = models.URLField(blank=True, verbose_name='External link')
    link_text = models.CharField(max_length=255, help_text='Text to display on the button for external links', blank=True)
    body = StreamField(LabBlock())

    content_panels = BasePage.content_panels + [
        ImageChooserPanel('icon'),
        FieldPanel('introduction'),
        MultiFieldPanel([
            PageChooserPanel('lab_type', 'funds.LabType'),
            FieldRowPanel([
                FieldPanel('lab_link'),
                FieldPanel('link_text'),
            ]),
        ], heading='Link for lab application'),
        StreamFieldPanel('body'),
        InlinePanel('related_pages', label="Related pages"),
    ]

    @property
    def is_open(self):
        return bool(self.lab_type.specific.open_round)

    def clean(self):
        if self.lab_type and self.lab_link:
            raise ValidationError({
                'lab_type': 'Cannot link to both a Lab page and external link',
                'lab_link': 'Cannot link to both a Lab page and external link',
            })

        if not self.lab_type and not self.lab_link:
            raise ValidationError({
                'lab_type': 'Please provide a way for applicants to apply',
                'lab_link': 'Please provide a way for applicants to apply',
            })

        if self.lab_type and self.link_text:
            raise ValidationError({
                'link_text': 'Cannot customise the text for internal lab pages, leave blank',
            })

        if self.lab_link and not self.link_text:
            raise ValidationError({
                'link_text': 'Please provide some text for the link button',
            })


class LabIndex(BasePage):
    subpage_types = ['LabPage']
    parent_page_types = ['home.HomePage']

    introduction = models.TextField(blank=True)

    content_panels = BasePage.content_panels + [
        FieldPanel('introduction')
    ]

    def get_context(self, request, *args, **kwargs):
        labs = LabPage.objects.live().public().descendant_of(self)

        # Pagination
        page = request.GET.get('page', 1)
        paginator = Paginator(labs, settings.DEFAULT_PER_PAGE)
        try:
            labs = paginator.page(page)
        except PageNotAnInteger:
            labs = paginator.page(1)
        except EmptyPage:
            labs = paginator.page(paginator.num_pages)

        context = super().get_context(request, *args, **kwargs)
        context.update(subpages=labs)
        return context
