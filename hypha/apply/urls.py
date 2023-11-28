from django.conf import settings
from django.urls import include, path, reverse_lazy
from django.views.generic import RedirectView
from two_factor.urls import urlpatterns as tf_urls

from hypha.urls import base_urlpatterns

from .api import urls as api_urls
from .dashboard import urls as dashboard_urls
from .users import urls as users_urls
from .utils import views

urlpatterns = [
    path("apply/", include("hypha.apply.funds.urls", "apply")),
    path("activity/", include("hypha.apply.activity.urls", "activity")),
    path("", include(users_urls)),
    path("api/", include(api_urls)),
    path("dashboard/", include(dashboard_urls)),
    path("hijack/", include("hijack.urls", "hijack")),
    # this must be above two factor include, this skip displaying the success
    # page and advances user to download backup code page.
    path(
        "account/two_factor/setup/complete/",
        RedirectView.as_view(url=reverse_lazy("users:backup_tokens"), permanent=False),
        name="two_factor:setup_complete",
    ),
    path("", include(tf_urls, "two_factor")),
]

if settings.DEBUG:
    urlpatterns += [
        # Add views for testing 404 and 500 templates
        path("test404/", views.page_not_found),
    ]

urlpatterns += base_urlpatterns


handler404 = "hypha.apply.utils.views.page_not_found"
handler403 = "hypha.apply.utils.views.permission_denied"
