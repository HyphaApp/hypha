from django.conf.urls import url

from wagtail.core import hooks

from .admin_views import index


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^users/$', index, name='index'),
    ]
