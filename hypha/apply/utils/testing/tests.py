from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory, TestCase, override_settings
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


@override_settings(ROOT_URLCONF='hypha.apply.urls')
class BaseViewTestCase(TestCase):
    """
    Provides a basic framework for working with views. It works on the
    assumption that view paths are similarly named e.g. my_view:detail and
    my_view:edit.

    Configure using:

    url_name:str = resolvable url path with one set of "{}", e.g.
    "path:to:view:{}"

    base_view_name:str = will replace the "{}" in url_name

    user_factory:() => User = Callable which will return a User object. If no
    user_factory is defined an anonymous user will be user
    """
    url_name = ''
    base_view_name = ''
    user_factory = None

    @classmethod
    def setUpTestData(cls):
        if not self.user_factory:
            cls.user = AnonymousUser()
        else:
            cls.user = cls.user_factory()
        super().setUpTestData()

    def setUp(self):
        if not self.user.is_anonymous:
            self.client.force_login(self.user)
        self.factory = RequestFactory()

    def get_kwargs(self, instance):
        return {}

    def url(self, instance, view_name=None, absolute=True, url_kwargs=None):
        view = view_name or self.base_view_name
        full_url_name = self.url_name.format(view)
        kwargs_method = f'get_{view}_kwargs'
        if hasattr(self, kwargs_method):
            kwargs = getattr(self, kwargs_method)(instance)
        else:
            kwargs = self.get_kwargs(instance)
        if url_kwargs:
            kwargs.update(url_kwargs)
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

    def get_page(self, instance=None, view_name=None, url_kwargs=None):
        return self.client.get(self.url(instance, view_name, url_kwargs=url_kwargs), secure=True, follow=True)

    def post_page(self, instance=None, data=dict(), view_name=None, url_kwargs=None):
        return self.client.post(self.url(instance, view_name, url_kwargs=url_kwargs), data, secure=True, follow=True)

    def refresh(self, instance):
        return instance.__class__.objects.get(id=instance.id)
