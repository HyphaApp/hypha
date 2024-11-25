import djp
from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django_file_form import urls as django_file_form_urls
from two_factor.urls import urlpatterns as tf_urls
from two_factor.views import LoginView
from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.contrib.sitemaps.views import sitemap
from wagtail.documents import urls as wagtaildocs_urls
from wagtail.images.views.serve import ServeView

from hypha.apply.api import urls as api_urls
from hypha.apply.dashboard import urls as dashboard_urls
from hypha.apply.users.urls import urlpatterns as user_urls
from hypha.apply.users.views import become, oauth_complete
from hypha.apply.utils.views import custom_wagtail_page_delete
from hypha.home.views import home

urlpatterns = [
    path("", home, name="home"),
    path("apply/", include("hypha.apply.funds.urls", "apply")),
    path("activity/", include("hypha.apply.activity.urls", "activity")),
    path("todo/", include("hypha.apply.todo.urls", "todo")),
    path("api/", include(api_urls)),
    path("django-admin/", admin.site.urls),
    path(
        "admin/login/",
        LoginView.as_view(
            template_name="users/login.html", redirect_authenticated_user=True
        ),
        name="wagtailadmin_login",
    ),
    path("admin/pages/<int:page_id>/delete/", custom_wagtail_page_delete),
    path("admin/", include(wagtailadmin_urls)),
    path("documents/", include(wagtaildocs_urls)),
    path("dashboard/", include(dashboard_urls)),
    path("sitemap.xml", sitemap),
    path("upload/", include(django_file_form_urls)),
    # path("complete/<str:backend>/", oauth_complete, name=f"{settings.SOCIAL_AUTH_URL_NAMESPACE}:complete"),
    path(
        "", include("social_django.urls", namespace=settings.SOCIAL_AUTH_URL_NAMESPACE)
    ),
    path("", include(tf_urls, "two_factor")),
    path("", include((user_urls, "users"))),
    path("tinymce/", include("tinymce.urls")),
    path("select2/", include("django_select2.urls")),
]

if settings.HIJACK_ENABLE:
    urlpatterns = [
        path("hijack/", include("hijack.urls", "hijack")),
        path("account/become/", become, name="hijack-become"),
    ] + urlpatterns

if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    from django.urls import get_callable
    from django.views import defaults as dj_default_views

    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    urlpatterns += [
        path(
            "test400/",
            dj_default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "test403/",
            dj_default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied!")},
        ),
        path("test403_csrf/", get_callable(settings.CSRF_FAILURE_VIEW)),
        path(
            "test404/",
            dj_default_views.page_not_found,
            kwargs={"exception": Exception("Not Found!")},
        ),
        path("test500/", dj_default_views.server_error),
    ]

# Override the social auth `<SOCIAL_NAMESPACE>:complete` to allow for extending the OAuth session
urlpatterns = [
    path(
        "complete/<str:backend>/",
        oauth_complete,
        name=f"{settings.SOCIAL_AUTH_URL_NAMESPACE}:complete",
    )
] + urlpatterns

urlpatterns += [
    re_path(
        r"^images/([^/]*)/(\d*)/([^/]*)/[^/]*$",
        ServeView.as_view(),
        name="wagtailimages_serve",
    ),
]

urlpatterns += [
    path("", include(wagtail_urls)),
]

# Load urls from any djp plugins.
urlpatterns += djp.urlpatterns()

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
        path("__reload__/", include("django_browser_reload.urls")),
    ] + urlpatterns


base_urlpatterns = [*urlpatterns]
