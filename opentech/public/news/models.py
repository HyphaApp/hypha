from django.db import models
from django.db.models.functions import Coalesce
from django.conf import settings
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator

from modelcluster.fields import ParentalKey

from wagtail.core.models import Orderable
from wagtail.core.fields import StreamField
from wagtail.admin.edit_handlers import (
    InlinePanel,
    FieldPanel,
    PageChooserPanel,
    StreamFieldPanel,
)
from wagtail.search import index

from opentech.public.utils.models import BasePage, RelatedPage
from opentech.public.utils.blocks import StoryBlock


class NewsType(models.Model):
    title = models.CharField(max_length=128)

    def __str__(self):
        return self.title


class NewsPageNewsType(models.Model):
    page = ParentalKey(
        'news.NewsPage',
        related_name='news_types'
    )
    news_type = models.ForeignKey(
        'NewsType',
        related_name='+',
        on_delete=models.CASCADE
    )

    panels = [
        FieldPanel('news_type')
    ]

    def __str__(self):
        return self.news_type.title


class NewsPageRelatedPage(RelatedPage):
    source_page = ParentalKey(
        'news.NewsPage',
        related_name='related_pages'
    )


class NewsProjectRelatedPage(RelatedPage):
    page = models.ForeignKey(
        'wagtailcore.Page',
        on_delete=models.CASCADE,
        related_name='news_mentions',
    )
    source_page = ParentalKey(
        'news.NewsPage',
        related_name='related_projects'
    )

    panels = [
        PageChooserPanel('page', 'projects.ProjectPage'),
    ]


class NewsPageAuthor(Orderable):
    source_page = ParentalKey(
        'news.NewsPage',
        related_name='authors'
    )
    author = models.ForeignKey(
        'wagtailcore.Page',
        on_delete=models.PROTECT,
        related_name='+',
    )

    panels = [
        PageChooserPanel('author', 'people.PersonPage')
    ]


class NewsPage(BasePage):
    subpage_types = []
    parent_page_types = ['NewsIndex']

    drupal_id = models.IntegerField(null=True, blank=True, editable=False)

    # It's datetime for easy comparison with first_published_at
    publication_date = models.DateTimeField(
        null=True, blank=True,
        help_text="Use this field to override the date that the "
        "news item appears to have been published."
    )
    introduction = models.TextField(blank=True)
    body = StreamField(StoryBlock())

    search_fields = BasePage.search_fields + [
        index.SearchField('introduction'),
        index.SearchField('body')
    ]

    content_panels = BasePage.content_panels + [
        FieldPanel('publication_date'),
        InlinePanel('authors', label="Authors"),
        FieldPanel('introduction'),
        StreamFieldPanel('body'),
        InlinePanel('news_types', label="News types"),
        InlinePanel('related_projects', label="Mentioned project"),
        InlinePanel('related_pages', label="Related pages"),
    ]

    @property
    def display_date(self):
        if self.publication_date:
            return self.publication_date
        else:
            return self.first_published_at


class NewsIndex(BasePage):
    subpage_types = ['NewsPage']
    parent_page_types = ['home.HomePage']

    introduction = models.TextField(blank=True)

    content_panels = BasePage.content_panels + [
        FieldPanel('introduction')
    ]

    def get_context(self, request, *args, **kwargs):
        news = NewsPage.objects.live().public().descendant_of(self).annotate(
            date=Coalesce('publication_date', 'first_published_at')
        ).order_by('-date').prefetch_related(
            'news_types__news_type',
            'authors__author',
        )

        if request.GET.get('news_type'):
            news = news.filter(news_types__news_type=request.GET.get('news_type'))

        # Pagination
        page = request.GET.get('page', 1)
        paginator = Paginator(news, settings.DEFAULT_PER_PAGE)
        try:
            news = paginator.page(page)
        except PageNotAnInteger:
            news = paginator.page(1)
        except EmptyPage:
            news = paginator.page(paginator.num_pages)

        context = super().get_context(request, *args, **kwargs)
        context.update(
            news=news,
            # Only show news types that have been used
            news_types=NewsPageNewsType.objects.all().values_list(
                'news_type__pk', 'news_type__title'
            ).distinct()
        )
        return context
