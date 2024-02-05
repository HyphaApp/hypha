from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import TemplateView
from django_file_form import urls as django_file_form_urls
from two_factor.views import LoginView
from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.contrib.sitemaps.views import sitemap
from wagtail.documents import urls as wagtaildocs_urls
from wagtail.images.views.serve import ServeView

from hypha.apply.api import urls as api_urls
from hypha.apply.dashboard import urls as dashboard_urls
from hypha.apply.users.urls import urlpatterns as user_urls
from hypha.apply.users.views import become
from hypha.apply.utils.views import custom_wagtail_page_delete

handler404 = "hypha.apply.utils.views.page_not_found"
handler403 = "hypha.apply.utils.views.permission_denied"

urlpatterns = [
    path("apply/", include("hypha.apply.funds.urls", "apply")),
    path("activity/", include("hypha.apply.activity.urls", "activity")),
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
    path("", include("social_django.urls", namespace="social")),
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

    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    urlpatterns += [
        # Add views for testing 404 and 500 templates
        path("test404/", TemplateView.as_view(template_name="404.html")),
        path("test500/", TemplateView.as_view(template_name="500.html")),
    ]

if settings.DEBUG or settings.ENABLE_STYLEGUIDE:
    urlpatterns += [
        # Add styleguide
        path("styleguide/", TemplateView.as_view(template_name="styleguide.html")),
    ]

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


if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
        path("__reload__/", include("django_browser_reload.urls")),
    ] + urlpatterns


base_urlpatterns = [*urlpatterns]
