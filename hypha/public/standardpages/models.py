from django.conf import settings
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import models
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from pagedown.widgets import PagedownWidget
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.fields import StreamField
from wagtail.search import index

from hypha.public.utils.blocks import StoryBlock
from hypha.public.utils.models import BasePage, RelatedPage


class InformationPageRelatedPage(RelatedPage):
    source_page = ParentalKey('InformationPage', related_name='related_pages')


class InformationPage(BasePage):
    introduction = models.TextField(blank=True)
    body = StreamField(StoryBlock(), use_json_field=True)

    search_fields = BasePage.search_fields + [
        index.SearchField('introduction'),
        index.SearchField('body'),
    ]

    content_panels = BasePage.content_panels + [
        FieldPanel('introduction'),
        FieldPanel('body'),
        InlinePanel('related_pages', label=_('Related pages')),
    ]


class IndexPage(BasePage):
    introduction = models.TextField(blank=True)

    content_panels = BasePage.content_panels + [
        FieldPanel('introduction', widget=PagedownWidget()),
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
