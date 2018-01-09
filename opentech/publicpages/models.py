from django.conf import settings
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import models

from wagtail.wagtailadmin.edit_handlers import (
    FieldPanel,
    PageChooserPanel,
    StreamFieldPanel,
)
from wagtail.wagtailcore.fields import StreamField

from opentech.utils.models import BasePage

from .blocks import FundBlock


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
        PageChooserPanel('fund_type', 'apply.FundType'),
        StreamFieldPanel('body'),
    ]


class FundIndex(BasePage):
    subpage_types = ['FundPage']
    parent_page_types = ['home.HomePage']

    def get_context(self, request, *args, **kwargs):
        funds = FundPage.objects.live().public().descendant_of(self)

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
