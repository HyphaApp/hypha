from django.urls import include, path

from .mailchimp import urls as newsletter_urls
from .news import feeds as news_feeds
from .partner import views as partner_views

urlpatterns = [
    path("news/feed/", news_feeds.NewsFeed(), name="news_feed"),
    path(
        "news/<int:news_type>/feed/", news_feeds.NewsTypeFeed(), name="news_type_feed"
    ),
    path("newsletter/", include(newsletter_urls)),
    path(
        "about/portfolio/",
        partner_views.InvestmentTableView.as_view(),
        name="investments",
    ),
]
