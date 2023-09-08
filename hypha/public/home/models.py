import datetime

from django.db import models
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import (
    FieldPanel,
    InlinePanel,
    MultiFieldPanel,
    PageChooserPanel,
)
from wagtail.fields import StreamField
from wagtail.search import index

from hypha.public.funds.models import FundPage, LabPage, RFPPage
from hypha.public.utils.models import BasePage, RelatedPage

from .blocks import OurWorkBlock


class PromotedFunds(RelatedPage):
    source_page = ParentalKey("home.HomePage", related_name="promoted_funds")

    class Meta(RelatedPage.Meta):
        unique_together = ("page",)

    panels = [
        PageChooserPanel("page", "public_funds.FundPage"),
    ]


class PromotedLabs(RelatedPage):
    source_page = ParentalKey("home.HomePage", related_name="promoted_labs")

    class Meta(RelatedPage.Meta):
        unique_together = ("page",)

    panels = [
        PageChooserPanel("page", "public_funds.LabPage"),
    ]


class PromotedRFPs(RelatedPage):
    source_page = ParentalKey("home.HomePage", related_name="promoted_rfps")

    class Meta(RelatedPage.Meta):
        unique_together = ("page",)

    panels = [
        PageChooserPanel("page", "public_funds.RFPPage"),
    ]


class HomePage(BasePage):
    # Only allow creating HomePages at the root level
    parent_page_types = ["wagtailcore.Page"]

    NUM_RELATED = 6

    strapline = models.CharField(blank=True, max_length=255)
    strapline_link = models.ForeignKey(
        "wagtailcore.Page", related_name="+", on_delete=models.PROTECT
    )
    strapline_link_text = models.CharField(max_length=255)

    news_title = models.CharField(blank=True, max_length=255)
    news_link = models.ForeignKey(
        "wagtailcore.Page",
        blank=True,
        null=True,
        related_name="+",
        on_delete=models.PROTECT,
    )
    news_link_text = models.CharField(blank=True, max_length=255)

    our_work_title = models.CharField(max_length=255)
    our_work = StreamField(
        [
            ("work", OurWorkBlock()),
        ],
        use_json_field=True,
    )
    our_work_link = models.ForeignKey(
        "wagtailcore.Page", related_name="+", on_delete=models.PROTECT
    )
    our_work_link_text = models.CharField(max_length=255)

    funds_title = models.CharField(max_length=255)
    funds_intro = models.TextField(blank=True)
    funds_link = models.ForeignKey(
        "wagtailcore.Page", related_name="+", on_delete=models.PROTECT
    )
    funds_link_text = models.CharField(max_length=255)

    labs_title = models.CharField(max_length=255)
    labs_intro = models.TextField(blank=True)
    labs_link = models.ForeignKey(
        "wagtailcore.Page", related_name="+", on_delete=models.PROTECT
    )
    labs_link_text = models.CharField(max_length=255)

    rfps_title = models.CharField(max_length=255)
    rfps_intro = models.TextField(blank=True)

    search_fields = BasePage.search_fields + [
        index.SearchField("strapline"),
    ]

    content_panels = BasePage.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("strapline"),
                PageChooserPanel("strapline_link"),
                FieldPanel("strapline_link_text"),
            ],
            heading=_("Introduction"),
        ),
        MultiFieldPanel(
            [
                FieldPanel("news_title"),
                PageChooserPanel("news_link"),
                FieldPanel("news_link_text"),
            ],
            heading=_("News"),
        ),
        MultiFieldPanel(
            [
                FieldPanel("our_work_title"),
                FieldPanel("our_work"),
                PageChooserPanel("our_work_link"),
                FieldPanel("our_work_link_text"),
            ],
            heading=_("Our Work"),
        ),
        MultiFieldPanel(
            [
                FieldPanel("funds_title"),
                FieldPanel("funds_intro"),
                InlinePanel(
                    "promoted_funds", label=_("Promoted Funds"), max_num=NUM_RELATED
                ),
                PageChooserPanel("funds_link"),
                FieldPanel("funds_link_text"),
            ],
            heading=_("Funds"),
        ),
        MultiFieldPanel(
            [
                FieldPanel("labs_title"),
                FieldPanel("labs_intro"),
                InlinePanel(
                    "promoted_labs", label=_("Promoted Labs"), max_num=NUM_RELATED
                ),
                PageChooserPanel("labs_link"),
                FieldPanel("labs_link_text"),
            ],
            heading=_("Labs"),
        ),
        MultiFieldPanel(
            [
                FieldPanel("rfps_title"),
                FieldPanel("rfps_intro"),
                InlinePanel(
                    "promoted_rfps", label=_("Promoted RFPs"), max_num=NUM_RELATED
                ),
            ],
            heading=_("Labs"),
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

    def get_context(self, *args, **kwargs):
        context = super().get_context(*args, **kwargs)
        context["lab_list"] = list(self.get_related(LabPage, self.promoted_labs))
        context["fund_list"] = list(self.get_related(FundPage, self.promoted_funds))
        context["rfps_list"] = list(self.get_related(RFPPage, self.promoted_rfps))
        return context
