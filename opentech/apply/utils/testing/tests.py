from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.auth.models import AnonymousUser
from django.test import override_settings, TestCase, RequestFactory
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


@override_settings(ROOT_URLCONF='opentech.apply.urls')
class BaseViewTestCase(TestCase):
    url_name = ''  # resolvable url, you should use "path:to:view:{}" and {} with be replaced with base_view_name
    base_view_name = ''
    user_factory = None

    @classmethod
    def setUpTestData(cls):
        cls.user = cls.user_factory()
        super().setUpTestData()

    def setUp(self):
        self.client.force_login(self.user)
        self.factory = RequestFactory()

    def get_kwargs(self, instance):
        return {}

    def url(self, instance, view_name=None, absolute=True, kwargs=dict()):
        view = view_name or self.base_view_name
        full_url_name = self.url_name.format(view)
        kwargs_method = f'get_{view}_kwargs'
        if hasattr(self, kwargs_method):
            kwargs = getattr(self, kwargs_method)(instance)
        else:
            kwargs = self.get_kwargs(instance)
        return self.url_from_pattern(full_url_name, kwargs, secure=True, absolute=absolute)

    def absolute_url(self, location, secure=True):
        request = self.factory.get(location, secure=secure)
        return request.build_absolute_uri()

    def url_from_pattern(self, pattern, kwargs=None, secure=True, absolute=True):
        url = reverse(pattern, kwargs=kwargs)
        if absolute:
            return self.absolute_url(url)
        request = self.factory.get(url, secure=secure)
        return request.path

    def get_page(self, instance=None, view_name=None):
        return self.client.get(self.url(instance, view_name), secure=True, follow=True)

    def post_page(self, instance=None, data=dict(), view_name=None):
        return self.client.post(self.url(instance, view_name), data, secure=True, follow=True)

    def refresh(self, instance):
        return instance.__class__.objects.get(id=instance.id)
