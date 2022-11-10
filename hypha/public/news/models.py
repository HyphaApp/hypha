from django.conf import settings
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import models
from django.db.models.functions import Coalesce
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from pagedown.widgets import PagedownWidget
from wagtail.admin.panels import FieldPanel, InlinePanel, PageChooserPanel
from wagtail.contrib.settings.models import BaseSetting
from wagtail.fields import StreamField
from wagtail.models import Orderable
from wagtail.search import index

from hypha.core.wagtail.admin import register_public_site_setting
from hypha.public.utils.models import BasePage, RelatedPage

from .blocks import NewsStoryBlock


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
        help_text=_('Use this field to override the date that the news item appears to have been published.')
    )
    introduction = models.TextField(blank=True)
    body = StreamField(
        NewsStoryBlock(block_counts={'awesome_table_widget': {'max_num': 1}}),
        use_json_field=True
    )

    search_fields = BasePage.search_fields + [
        index.SearchField('introduction'),
        index.SearchField('body')
    ]

    content_panels = BasePage.content_panels + [
        FieldPanel('publication_date'),
        InlinePanel('authors', label=_('Authors')),
        FieldPanel('introduction'),
        FieldPanel('body'),
        InlinePanel('news_types', label=_('News types')),
        InlinePanel('related_projects', label=_('Mentioned project')),
        InlinePanel('related_pages', label=_('Related pages')),
    ]

    @property
    def display_date(self):
        if self.publication_date:
            return self.publication_date
        else:
            return self.first_published_at

    def get_absolute_url(self):
        return self.full_url


class NewsIndex(BasePage):
    subpage_types = ['NewsPage']
    parent_page_types = ['home.HomePage']

    introduction = models.TextField(blank=True)

    content_panels = BasePage.content_panels + [
        FieldPanel('introduction', widget=PagedownWidget())
    ]

    def get_context(self, request, *args, **kwargs):
        news = NewsPage.objects.live().public().descendant_of(self).annotate(
            date=Coalesce('publication_date', 'first_published_at')
        ).order_by('-date').prefetch_related(
            'news_types__news_type',
            'authors__author',
        )

        if request.GET.get('news_type') and request.GET.get('news_type').isdigit():
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


@register_public_site_setting
class NewsFeedSettings(BaseSetting):
    news_title = models.CharField(max_length=255, help_text=_('The title of the main news feed.'))
    news_description = models.CharField(max_length=255, help_text=_('The description of the main news feed.'))

    news_per_type_title = models.CharField(
        max_length=255, help_text=_('The title of the news feed by type. Use {news_type} to insert the type name.'))
    news_per_type_description = models.CharField(
        max_length=255, help_text=_('The description of the news feed by type. Use {news_type} to insert the type name.'))
