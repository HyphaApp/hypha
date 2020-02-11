from django.conf import settings
from django.urls import include, path

from two_factor.urls import urlpatterns as tf_urls

from .utils import views
from .users import urls as users_urls
from .dashboard import urls as dashboard_urls
from .api import urls as api_urls

from hypha.urls import base_urlpatterns


urlpatterns = [
    path('apply/', include('hypha.apply.funds.urls', 'apply')),
    path('activity/', include('hypha.apply.activity.urls', 'activity')),
    path('', include(users_urls)),
    path('api/', include(api_urls)),
    path('dashboard/', include(dashboard_urls)),
    path('hijack/', include('hijack.urls', 'hijack')),
    path('', include(tf_urls, 'two_factor')),
]

if settings.DEBUG:
    urlpatterns += [
        # Add views for testing 404 and 500 templates
        path('test404/', views.page_not_found),
    ]

urlpatterns += base_urlpatterns


handler404 = 'hypha.apply.utils.views.page_not_found'
