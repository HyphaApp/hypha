from django.contrib.syndication.views import Feed

from opentech.public.news.models import NewsPage, NewsType


class NewsFeed(Feed):
    link = "https://www.opentech.fund/news/"
    title = "OTF – News, updates, and announcements"
    description = "News, updates, and announcements from The Open Technology Fund"

    def items(self):
        return NewsPage.objects.live().order_by('-first_published_at')[:20]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.body

    def item_pubdate(self, item):
        return item.display_date


class NewsTypesFeed(Feed):
    link = "https://www.opentech.fund/news/"

    def get_object(self, request, type):
        return NewsType.objects.get(id=type)

    def title(self, type):
        return f"OTF – News of type {type}"

    def description(self, type):
        return f"News, updates, and announcements of type {type} from The Open Technology Fund"

    def items(self, type):
        return NewsPage.objects.live().filter(news_types__news_type=type).order_by('-first_published_at')[:20]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.body

    def item_pubdate(self, item):
        return item.display_date
