from django.db import models
from django.conf import settings
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator

from modelcluster.fields import ParentalKey
from wagtail.wagtailadmin.edit_handlers import (
    FieldPanel,
    InlinePanel,
    PageChooserPanel,
    StreamFieldPanel,
)

from wagtail.wagtailcore.fields import StreamField
from wagtail.wagtailsearch import index

from opentech.utils.blocks import StoryBlock
from opentech.utils.models import (
    BasePage,
    RelatedPage,
)


class ProjectPageRelatedPage(RelatedPage):
    source_page = ParentalKey('ProjectPage', related_name='related_pages')

    panels = [
        PageChooserPanel('page', 'projects.ProjectPage'),
    ]


class ProjectPage(BasePage):
    subpage_types = []
    parent_page_types = ['ProjectIndexPage']

    introduction = models.TextField(blank=True)
    body = StreamField(StoryBlock())

    # Fields to add:
    # otf_status
    # status
    # social_accounts
    # website
    # funding

    search_fields = BasePage.search_fields + [
        index.SearchField('introduction'),
        index.SearchField('body'),
    ]

    content_panels = BasePage.content_panels + [
        FieldPanel('introduction'),
        StreamFieldPanel('body'),
        InlinePanel('related_pages', label="Related pages"),
    ]


class ProjectIndexPage(BasePage):

    introduction = models.TextField(blank=True)

    content_panels = BasePage.content_panels + [
        FieldPanel('introduction'),
    ]

    search_fields = BasePage.search_fields + [
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
