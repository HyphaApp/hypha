from django.urls import include, path

from .news import views as news_views
from .search import views as search_views
from .mailchimp import urls as newsletter_urls


urlpatterns = [
    path('search/', search_views.search, name='search'),
    path('news/feed/', news_views.NewsFeed(), name='news_feed'),
    path('news/<int:news_type>/feed/', news_views.NewsTypeFeed(), name='news_types_feed'),
    path('newsletter/', include(newsletter_urls))
]
