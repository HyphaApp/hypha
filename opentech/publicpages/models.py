from django.conf import settings
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import models
from django.db.models.functions import Coalesce

from wagtail.wagtailadmin.edit_handlers import (
    FieldPanel,
    PageChooserPanel,
    StreamFieldPanel,
)
from wagtail.wagtailcore.fields import StreamField

from opentech.utils.blocks import StoryBlock
from opentech.utils.models import BasePage


class FundPage(BasePage):
    subpage_types = []
    parent_page_types = ['FundIndex']

    introduction = models.TextField(blank=True)
    fund_type = models.ForeignKey(
        'wagtailcore.Page',
        on_delete=models.SET_NULL,
        related_name='+',
    )
    body = StreamField(StoryBlock())

    content_panels = BasePage.content_panels + [
        FieldPanel('introduction'),
        PageChooserPanel('fund_type', 'apply.FundType'),
        StreamFieldPanel('body'),
    ]


class NewsIndex(BasePage):
    subpage_types = ['FundPage']
    parent_page_types = ['home.HomePage']

    def get_context(self, request, *args, **kwargs):
        funds = FundPage.objects.live().public().descendant_of(self).annotate(
            date=Coalesce('publication_date', 'first_published_at')
        ).order_by('-date')

        # Pagination
        page = request.GET.get('page', 1)
        paginator = Paginator(funds, settings.DEFAULT_PER_PAGE)
        try:
            news = paginator.page(page)
        except PageNotAnInteger:
            news = paginator.page(1)
        except EmptyPage:
            news = paginator.page(paginator.num_pages)

        context = super().get_context(request, *args, **kwargs)
        context.update(news=news)
        return context
