from django.urls import include, path

from .users import urls as users_urls
from .dashboard import urls as dashboard_urls

from opentech.urls import base_urlpatterns


urlpatterns = [
    path('apply/', include('opentech.apply.funds.urls', 'apply')),
    path('activity/', include('opentech.apply.activity.urls', 'activity')),
    path('', include(users_urls)),
    path('dashboard/', include(dashboard_urls)),
    path('hijack/', include('hijack.urls', 'hijack')),
]

urlpatterns += base_urlpatterns
