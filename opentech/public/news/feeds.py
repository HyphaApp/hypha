from django.conf import settings
from django.contrib.syndication.views import Feed
from django.core.cache import cache
from django.db.models.functions import Coalesce
from django.http import Http404

from wagtail.core.models import Site

from opentech.public.news.models import NewsPage, NewsType, NewsIndex, NewsFeedSettings


class NewsFeed(Feed):
    def __call__(self, request, *args, **kwargs):
        try:
            self.site = Site.objects.get(is_default_site=True)
        except Site.DoesNotExist:
            raise Http404
        self.news_feed_settings = NewsFeedSettings.for_site(site=self.site)

        cache_key = self.get_cache_key(*args, **kwargs)
        response = cache.get(cache_key)

        if response is None:
            response = super().__call__(request, *args, **kwargs)
            cache.set(cache_key, response, settings.FEED_CACHE_TIMEOUT)

        return response

    def get_cache_key(self, *args, **kwargs):
        tag = ''
        for key, value in kwargs.items():
            tag += f"-{key}-{value}"
        return f"{self.__class__.__module__}{tag}"

    def title(self):
        return self.news_feed_settings.news_title

    def description(self):
        return self.news_feed_settings.news_description

    def link(self):
        news_index = NewsIndex.objects.live().public().first()
        if news_index:
            return news_index.full_url
        return self.site.root_url

    def items(self):
        return NewsPage.objects.live().public().annotate(
            date=Coalesce('publication_date', 'first_published_at')
        ).order_by('-date')[:20]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.body

    def item_pubdate(self, item):
        return item.display_date


class NewsTypeFeed(NewsFeed):
    def get_object(self, request, news_type):
        return NewsType.objects.get(id=news_type)

    def title(self, obj):
        return self.news_feed_settings.news_per_type_title.format(news_type=obj)

    def description(self, obj):
        return self.news_feed_settings.news_per_type_description.format(news_type=obj)

    def link(self, obj):
        news_index = NewsIndex.objects.live().public().first()
        if news_index:
            return f"{news_index.full_url}?news_type={obj.id}"
        return self.site.root_url

    def items(self, obj):
        return NewsPage.objects.live().public().filter(news_types__news_type=obj).annotate(
            date=Coalesce('publication_date', 'first_published_at')
        ).order_by('-date')[:20]
