from django.urls import include, path

from .search import views as search_views
from .mailchimp import urls as newsletter_urls


urlpatterns = [
    path('search/', search_views.search, name='search'),
    path('newsletter/', include(newsletter_urls))
]
