from django.conf import settings
from django.db import models
from django.utils.decorators import method_decorator
from rest_framework_api_key.models import AbstractAPIKey
from wagtail.admin.edit_handlers import FieldPanel
from wagtail.core.models import Page
from wagtail.search import index
from wagtailcache.cache import WagtailCacheMixin, cache_page

from hypha.apply.funds.models import ApplicationBase, LabBase


@method_decorator(cache_page, name='serve')
class ApplyHomePage(WagtailCacheMixin, Page):
    # Only allow creating HomePages at the root level
    parent_page_types = ['wagtailcore.Page']
    subpage_types = ['funds.FundType', 'funds.LabType', 'funds.RequestForPartners']

    strapline = models.CharField(blank=True, max_length=255)

    search_fields = Page.search_fields + [
        index.SearchField('strapline'),
    ]

    content_panels = Page.content_panels + [
        FieldPanel('strapline'),
    ]

    def cache_control(self):
        return f'public, s-maxage={settings.CACHE_CONTROL_S_MAXAGE}'

    def get_context(self, *args, **kwargs):
        context = super().get_context(*args, **kwargs)
        context['open_funds'] = ApplicationBase.objects.order_by_end_date().prefetch_related(
            'application_public'
        ).specific()
        context['open_labs'] = LabBase.objects.public().live().prefetch_related(
            'lab_public'
        ).specific()
        return context


class ApplyAPIKey(AbstractAPIKey):
    home_page = models.ForeignKey(
        "apply_home.ApplyHomePage",
        on_delete=models.CASCADE,
        related_name="api_keys",
    )

    class Meta(AbstractAPIKey.Meta):
        verbose_name = "Apply HomePage API key"
        verbose_name_plural = "Apply HomePage API keys"
