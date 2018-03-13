from django.urls import include, path

from .funds import urls as funds_urls
from .users import urls as users_urls
from .dashboard import urls as dashboard_urls


urlpatterns = [
    path('apply/', include(funds_urls)),
    path('account/', include(users_urls)),
    path('dashboard/', include(dashboard_urls)),
]
