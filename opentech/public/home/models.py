from django.db import models

from modelcluster.fields import ParentalKey

from wagtail.wagtailadmin.edit_handlers import FieldPanel, InlinePanel, PageChooserPanel
from wagtail.wagtailsearch import index

from opentech.public.utils.models import BasePage, RelatedPage

from opentech.public.funds.models import FundPage, LabPage


class PromotedFunds(RelatedPage):
    source_page = ParentalKey(
        'home.HomePage',
        related_name='promoted_funds'
    )

    class Meta(RelatedPage.Meta):
        unique_together = ('page',)

    panels = [
        PageChooserPanel('page', 'public_funds.FundPage'),
    ]


class PromotedLabs(RelatedPage):
    source_page = ParentalKey(
        'home.HomePage',
        related_name='promoted_labs'
    )

    class Meta(RelatedPage.Meta):
        unique_together = ('page',)

    panels = [
        PageChooserPanel('page', 'public_funds.LabPage'),
    ]


class HomePage(BasePage):
    # Only allow creating HomePages at the root level
    parent_page_types = ['wagtailcore.Page']

    NUM_RELATED = 6

    strapline = models.CharField(blank=True, max_length=255)

    search_fields = BasePage.search_fields + [
        index.SearchField('strapline'),
    ]

    content_panels = BasePage.content_panels + [
        FieldPanel('strapline'),
        InlinePanel('promoted_funds', label='Promoted Funds', max_num=NUM_RELATED),
        InlinePanel('promoted_labs', label='Promoted Labs', max_num=NUM_RELATED),
    ]

    def get_related(self, page_type, base_list):
        yield from self.pages_from_related(base_list)
        selected = list(base_list.values_list('page', flat=True))
        extra_needed = self.NUM_RELATED - len(selected)
        yield from page_type.objects.exclude(id__in=selected)[:extra_needed]

    def pages_from_related(self, related):
        for related in related.all():
            yield related.page.specific

    def get_context(self, *args, **kwargs):
        context = super().get_context(*args, **kwargs)
        context['lab_list'] = self.get_related(LabPage, self.promoted_labs)
        context['fund_list'] = self.get_related(FundPage, self.promoted_funds)
        return context
