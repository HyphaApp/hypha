from django.contrib.syndication.views import Feed
from django.db.models.functions import Coalesce

from wagtail.core.models import Site

from opentech.public.news.models import NewsPage, NewsType, NewsIndex, NewsFeedSettings


class NewsFeed(Feed):
    site = Site.objects.get(is_default_site=True)
    news_feed_settings = NewsFeedSettings.for_site(site=site)
    news_index = NewsIndex.objects.first()
    link = f"{site.root_url}/{news_index.slug}/"
    title = news_feed_settings.news_title
    description = news_feed_settings.news_description

    def items(self):
        return NewsPage.objects.live().public().annotate(date=Coalesce('publication_date', 'first_published_at')).order_by('-date')[:20]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.body

    def item_pubdate(self, item):
        return item.display_date


class NewsTypesFeed(NewsFeed):
    site = Site.objects.get(is_default_site=True)
    news_feed_settings = NewsFeedSettings.for_site(site=site)
    news_index = NewsIndex.objects.first()

    def get_object(self, request, news_type):
        return NewsType.objects.get(id=news_type)

    def link(self, obj):
        return f"{self.site.root_url}/{self.news_index.slug}/?news_type={obj.id}"

    def title(self, obj):
        return self.news_feed_settings.news_per_type_title.format(news_type=obj)

    def description(self, obj):
        return self.news_feed_settings.news_per_type_description.format(news_type=obj)

    def items(self, obj):
        return NewsPage.objects.live().public().filter(news_types__news_type=obj).annotate(date=Coalesce('publication_date', 'first_published_at')).order_by('-date')[:20]
