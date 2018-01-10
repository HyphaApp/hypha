from django.conf.urls import include, url

from .funds import urls as funds_urls
from .users import urls as users_urls

urlpatterns = [
    url(r'^apply/', include(funds_urls)),
    url(r'^user/', include(users_urls))
]
