from django.urls import include, path

from .search import views as search_views
from .mailchimp import urls as newsletter_urls
from .news import feeds as news_feeds

urlpatterns = [
    path('search/', search_views.search, name='search'),
    path('news/feed/', news_feeds.NewsFeed(), name='news_feed'),
    path('news/<int:news_type>/feed/', news_feeds.NewsTypeFeed(), name='news_type_feed'),
    path('newsletter/', include(newsletter_urls))
]
