from django.conf.urls import url

from .esi import views as esi_views
from .search import views as search_views

urlpatterns = [
    url(r'^esi/(.*)/$', esi_views.esi, name='esi'),
    url(r'^search/$', search_views.search, name='search'),
]
