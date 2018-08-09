from django.urls import include, path

from .esi import views as esi_views
from .search import views as search_views
from .mailchimp import urls as newsletter_urls


urlpatterns = [
    path('esi/<slug>/', esi_views.esi, name='esi'),
    path('search/', search_views.search, name='search'),
    path('newsletter/', include(newsletter_urls))
]
