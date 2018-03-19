from django.urls import include, path

from .users import urls as users_urls
from .dashboard import urls as dashboard_urls


urlpatterns = [
    path('apply/', include('opentech.apply.funds.urls', 'apply')),
    path('account/', include(users_urls)),
    path('dashboard/', include(dashboard_urls)),
]
