from django.urls import include, path

from .users import urls as users_urls
from .dashboard import urls as dashboard_urls


urlpatterns = [
    path('apply/', include('opentech.apply.funds.urls', 'apply')),
    path('activity/', include('opentech.apply.activity.urls', 'activity')),
    path('account/', include(users_urls)),
    path('dashboard/', include(dashboard_urls)),
    path('hijack/', include('hijack.urls', 'hijack')),
]
