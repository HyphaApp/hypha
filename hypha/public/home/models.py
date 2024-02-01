import datetime

from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import (
    FieldPanel,
    MultiFieldPanel,
)
from wagtail.search import index

from hypha.public.utils.models import BasePage


class HomePage(BasePage):
    # Only allow creating HomePages at the root level
    parent_page_types = ["wagtailcore.Page"]

    NUM_RELATED = 6

    strapline = models.CharField(blank=True, max_length=255)

    news_title = models.CharField(blank=True, max_length=255)

    search_fields = BasePage.search_fields + [
        index.SearchField("strapline"),
    ]

    content_panels = BasePage.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("strapline"),
            ],
            heading=_("Introduction"),
        ),
        MultiFieldPanel(
            [
                FieldPanel("news_title"),
            ],
            heading=_("News"),
        ),
    ]

    def get_related(self, page_type, base_list):
        related = (
            page_type.objects.filter(id__in=base_list.values_list("page"))
            .live()
            .public()
        )
        yield from related
        selected = list(related.values_list("id", flat=True))
        extra_needed = self.NUM_RELATED - len(selected)
        extra_qs = page_type.objects.public().live().exclude(id__in=selected)
        displayed = 0
        for page in self.sorted_by_deadline(extra_qs):
            if page.is_open:
                yield page
                displayed += 1
            if displayed >= extra_needed:
                break

    def sorted_by_deadline(self, qs):
        def sort_by_deadline(value):
            try:
                return value.deadline or datetime.date.max
            except AttributeError:
                return datetime.date.max

        yield from sorted(qs, key=sort_by_deadline)

    def pages_from_related(self, related):
        for related_obj in related.all():
            if related_obj.page.live and related_obj.page.public:
                yield related_obj.page.specific
