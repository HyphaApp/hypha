from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.views.decorators.cache import cache_control
from django.views.generic import TemplateView

from wagtail.utils.urlpatterns import decorate_urlpatterns
from wagtail.contrib.wagtailsitemaps.views import sitemap
from wagtail.wagtailadmin import urls as wagtailadmin_urls
from wagtail.wagtailcore import urls as wagtail_urls
from wagtail.wagtaildocs import urls as wagtaildocs_urls

from opentech.public import urls as public_urls
from opentech.apply import urls as apply_urls


urlpatterns = [
    url(r'^django-admin/', include(admin.site.urls)),
    url(r'^admin/', include(wagtailadmin_urls)),

    url(r'^documents/', include(wagtaildocs_urls)),
    url('^sitemap\.xml$', sitemap),
    url('^', include(public_urls)),
    url('^', include(apply_urls)),
    url('^', include('social_django.urls', namespace='social')),
]


if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    urlpatterns += [
        # Add views for testing 404 and 500 templates
        url(r'^test404/$', TemplateView.as_view(template_name='404.html')),
        url(r'^test500/$', TemplateView.as_view(template_name='500.html')),
    ]

if settings.DEBUG or settings.ENABLE_STYLEGUIDE:
    urlpatterns += [
        # Add styleguide
        url(r'^styleguide/$', TemplateView.as_view(template_name='styleguide.html')),
    ]

urlpatterns += [
    url(r'', include(wagtail_urls)),
]


# Cache-control
cache_length = getattr(settings, 'CACHE_CONTROL_MAX_AGE', None)

if cache_length:
    urlpatterns = decorate_urlpatterns(
        urlpatterns,
        cache_control(max_age=cache_length)
    )
