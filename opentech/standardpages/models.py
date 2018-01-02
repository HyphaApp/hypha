from django.db import models
from django.conf import settings
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator

from modelcluster.fields import ParentalKey
from wagtail.wagtailadmin.edit_handlers import (
    FieldPanel, StreamFieldPanel,
    InlinePanel
)

from wagtail.wagtailcore.fields import StreamField
from wagtail.wagtailcore.models import Page
from wagtail.wagtailsearch import index

from opentech.utils.blocks import StoryBlock
from opentech.utils.models import (
    BasePage,
    RelatedPage,
)


class InformationPageRelatedPage(RelatedPage):
    source_page = ParentalKey('InformationPage', related_name='related_pages')


class InformationPage(BasePage):
    introduction = models.TextField(blank=True)
    body = StreamField(StoryBlock())

    search_fields = Page.search_fields + [
        index.SearchField('introduction'),
        index.SearchField('body'),
    ]

    content_panels = Page.content_panels + [
        FieldPanel('introduction'),
        StreamFieldPanel('body'),
        InlinePanel('related_pages', label="Related pages"),
    ]


class IndexPage(BasePage):
    introduction = models.TextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('introduction'),
    ]

    search_fields = Page.search_fields + [
        index.SearchField('introduction'),
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        subpages = self.get_children().live()
        per_page = settings.DEFAULT_PER_PAGE
        page_number = request.GET.get('page')
        paginator = Paginator(subpages, per_page)

        try:
            subpages = paginator.page(page_number)
        except PageNotAnInteger:
            subpages = paginator.page(1)
        except EmptyPage:
            subpages = paginator.page(paginator.num_pages)

        context['subpages'] = subpages

        return context
