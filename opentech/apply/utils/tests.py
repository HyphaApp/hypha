from django.test import TestCase, RequestFactory
from django.urls import reverse


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

    def url(self, instance, view_name=None):
        full_url_name = self.url_name.format(view_name or self.base_view_name)
        url = reverse(full_url_name, kwargs=self.get_kwargs(instance))
        request = self.factory.get(url, secure=True)
        return request.build_absolute_uri()

    def get_page(self, instance=None, view_name=None):
        return self.client.get(self.url(instance, view_name), secure=True, follow=True)

    def post_page(self, instance=None, data=dict(), view_name=None):
        return self.client.post(self.url(instance, view_name), data, secure=True, follow=True)

    def refresh(self, instance):
        return instance.__class__.objects.get(id=instance.id)
