from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory, TestCase
from django.urls import reverse

request_factory = RequestFactory()


def make_request(user=None, data=None, method="get", site=None):
    user = user or AnonymousUser()
    data = data or {}
    method = getattr(request_factory, method)
    request = method("", data)
    request.user = user
    request.site = site
    request.session = {}
    request._messages = FallbackStorage(request)
    return request


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

    url_name = ""
    base_view_name = ""
    user_factory = None
    user = None

    def setUp(self):
        self.factory = RequestFactory()
        if self.user_factory:
            self.user = self.user_factory()
        else:
            self.user = AnonymousUser()

        if not self.user.is_anonymous:
            self.client.force_login(self.user)

    def get_kwargs(self, instance):
        return {}

    def url(self, instance, view_name=None, absolute=False, url_kwargs=None):
        view = view_name or self.base_view_name
        full_url_name = self.url_name.format(view)
        kwargs_method = f"get_{view}_kwargs"
        if hasattr(self, kwargs_method):
            kwargs = getattr(self, kwargs_method)(instance)
        else:
            kwargs = self.get_kwargs(instance)
        if url_kwargs:
            kwargs.update(url_kwargs)
        return self.url_from_pattern(full_url_name, kwargs, absolute=absolute)

    def absolute_url(self, location, secure=False):
        request = self.factory.get(location, secure=secure)
        return request.build_absolute_uri()

    def url_from_pattern(self, pattern, kwargs=None, secure=False, absolute=False):
        url = reverse(pattern, kwargs=kwargs)
        if absolute:
            return self.absolute_url(url)
        request = self.factory.get(url, secure=secure)
        return request.path

    def get_page(self, instance=None, view_name=None, url_kwargs=None):
        return self.client.get(
            self.url(instance, view_name, url_kwargs=url_kwargs),
            secure=True,
            follow=True,
        )

    def post_page(self, instance=None, data=None, view_name=None, url_kwargs=None):
        data = data or {}
        return self.client.post(
            self.url(instance, view_name, url_kwargs=url_kwargs),
            data,
            secure=True,
            follow=True,
        )

    def refresh(self, instance):
        return instance.__class__.objects.get(id=instance.id)
