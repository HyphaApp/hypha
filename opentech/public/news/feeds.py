from django.contrib.syndication.views import Feed
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
        return super().__call__(request, *args, **kwargs)

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
            return news_index.full_url + '?news_type={}'.format(obj.id)
        return self.site.root_url

    def items(self, obj):
        return NewsPage.objects.live().public().filter(news_types__news_type=obj).annotate(
            date=Coalesce('publication_date', 'first_published_at')
        ).order_by('-date')[:20]
