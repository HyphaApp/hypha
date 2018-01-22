from django.conf.urls import include, url

from .funds import urls as funds_urls
from .users import urls as users_urls
from .dashboard import urls as dashboard_urls


urlpatterns = [
    url(r'^apply/', include(funds_urls)),
    url(r'^account/', include(users_urls, namespace='users')),
    url(r'^dashboard/', include(dashboard_urls, namespace='dashboard')),
]
