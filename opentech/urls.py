from django.conf import settings
from django.urls import include, path
from django.contrib import admin
from django.views.decorators.cache import cache_control
from django.views.generic import TemplateView

from wagtail.utils.urlpatterns import decorate_urlpatterns
from wagtail.contrib.sitemaps.views import sitemap
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.core import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls

from opentech.public import urls as public_urls
from opentech.apply import urls as apply_urls


urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('admin/', include(wagtailadmin_urls)),

    path('documents/', include(wagtaildocs_urls)),
    path('sitemap.xml', sitemap),
    path('', include(public_urls)),
    path('', include(apply_urls)),
    path('', include('social_django.urls', namespace='social')),
    path('tinymce/', include('tinymce.urls')),
    path('select2/', include('django_select2.urls')),
]


if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    urlpatterns += [
        # Add views for testing 404 and 500 templates
        path('test404/', TemplateView.as_view(template_name='404.html')),
        path('test500/', TemplateView.as_view(template_name='500.html')),
    ]

if settings.DEBUG or settings.ENABLE_STYLEGUIDE:
    urlpatterns += [
        # Add styleguide
        path('styleguide/', TemplateView.as_view(template_name='styleguide.html')),
    ]

urlpatterns += [
    path('', include(wagtail_urls)),
]


# Cache-control
cache_length = getattr(settings, 'CACHE_CONTROL_MAX_AGE', None)

if cache_length:
    urlpatterns = decorate_urlpatterns(
        urlpatterns,
        cache_control(max_age=cache_length)
    )
