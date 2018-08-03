from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase, RequestFactory
from django.urls import reverse


request_factory = RequestFactory()


def make_request(user=AnonymousUser(), data={}, method='get', site=None):
    method = getattr(request_factory, method)
    request = method('', data)
    request.user = user
    request.site = site
    request.session = {}
    request._messages = FallbackStorage(request)
    return request


class BaseViewTestCase(TestCase):
    url_name = ''  # resolvable url, you should use "path:to:view:{}" and {} with be replaced with base_view_name
    base_view_name = ''
    user_factory = None

    def setUp(self):
        self.factory = RequestFactory()
        self.user = self.user_factory()
        self.client.force_login(self.user)

    def get_kwargs(self, instance):
        return {}

    def url(self, instance, view_name=None, absolute=True):
        full_url_name = self.url_name.format(view_name or self.base_view_name)
        return self.url_from_pattern(full_url_name, self.get_kwargs(instance), secure=True, absolute=absolute)

    def url_from_pattern(self, pattern, kwargs=None, secure=True, absolute=True):
        url = reverse(pattern, kwargs=kwargs)
        request = self.factory.get(url, secure=secure)
        if absolute:
            return request.build_absolute_uri()
        return request.path

    def get_page(self, instance=None, view_name=None):
        return self.client.get(self.url(instance, view_name), secure=True, follow=True)

    def post_page(self, instance=None, data=dict(), view_name=None):
        return self.client.post(self.url(instance, view_name), data, secure=True, follow=True)

    def refresh(self, instance):
        return instance.__class__.objects.get(id=instance.id)
