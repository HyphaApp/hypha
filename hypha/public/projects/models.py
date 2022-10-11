import json

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.core.validators import URLValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from pagedown.widgets import PagedownWidget
from wagtail.admin.panels import (
    FieldPanel,
    InlinePanel,
    MultiFieldPanel,
    PageChooserPanel,
)
from wagtail.fields import StreamField
from wagtail.search import index

from hypha.apply.categories.models import Option
from hypha.public.utils.blocks import StoryBlock
from hypha.public.utils.models import BaseFunding, BasePage, FundingMixin, RelatedPage

from .widgets import CategoriesWidget


class ProjectContactDetails(models.Model):
    project_page = ParentalKey(
        'ProjectPage',
        related_name='contact_details'
    )
    site_titles = (
        ('website', "Main Website URL"),
        ('twitter', "Twitter Handle"),
        ('github', "Github Organisation or Project"),
    )
    site_urls = (
        ('website', ''),
        ('twitter', 'https://twitter.com/'),
        ('github', 'https://github.com/'),
    )
    service = models.CharField(
        max_length=200,
        choices=site_titles,
    )
    value = models.CharField(max_length=255)

    @property
    def url(self):
        return dict(self.site_urls)[self.service] + self.value

    def service_name(self):
        site_display = {
            'twitter': '@' + self.value,
            'github': 'Github',
            'website': 'Main Website',
        }
        return site_display[self.service]

    def clean(self):
        if self.service == 'twitter' and self.value.startswith('@'):
            self.username = self.username[1:]

        if self.service == 'website':
            validate = URLValidator()
            try:
                validate(self.value)
            except ValidationError as e:
                raise ValidationError({'value': e})


class ProjectPageRelatedPage(RelatedPage):
    source_page = ParentalKey('ProjectPage', related_name='related_pages')

    panels = [
        PageChooserPanel('page', 'projects.ProjectPage'),
    ]


class ProjectFundingQueryset(models.QuerySet):
    def projects(self):
        return ProjectPage.objects.filter(id__in=self.values_list('page__id')).live().public()


class ProjectFunding(BaseFunding):
    page = ParentalKey('ProjectPage', related_name='funding')

    objects = ProjectFundingQueryset.as_manager()


class ProjectPage(FundingMixin, BasePage):
    STATUSES = (
        ('idea', "Just an Idea. (Pre-alpha)"),
        ('exists', "It Exists! (Alpha/Beta)"),
        ('release', "It's basically done. (Release)"),
        ('production', "People Use it. (Production)"),
    )

    subpage_types = []
    parent_page_types = ['ProjectIndexPage']

    drupal_id = models.IntegerField(null=True, blank=True, editable=False)

    introduction = models.TextField(blank=True)
    icon = models.ForeignKey(
        'images.CustomImage',
        null=True,
        blank=True,
        related_name='+',
        on_delete=models.SET_NULL
    )
    status = models.CharField(choices=STATUSES, max_length=25, default=STATUSES[0][0])
    body = StreamField(StoryBlock(), use_json_field=True)

    categories = models.TextField(default='{}', blank=True)

    search_fields = BasePage.search_fields + [
        index.SearchField('introduction'),
        index.SearchField('body'),
    ]

    content_panels = BasePage.content_panels + [
        FieldPanel('icon'),
        FieldPanel('status'),
        FieldPanel('introduction'),
        FieldPanel('body'),
        InlinePanel('contact_details', label=_('Contact Details')),
    ] + FundingMixin.content_panels + [
        InlinePanel('related_pages', label=_('Related Projects')),
        MultiFieldPanel(
            [FieldPanel('categories', widget=CategoriesWidget)],
            heading=_('Categories'),
            classname="collapsible collapsed",
        ),
    ]

    def category_options(self):
        categories = json.loads(self.categories)
        options = [int(id) for options in categories.values() for id in options]
        return Option.objects.select_related().filter(id__in=options).order_by('category_id', 'sort_order')


class ProjectIndexPage(BasePage):
    subpage_types = ['ProjectPage']
    parent_page_types = ['home.Homepage', 'standardpages.IndexPage']

    introduction = models.TextField(blank=True)

    content_panels = BasePage.content_panels + [
        FieldPanel('introduction', widget=PagedownWidget()),
    ]

    search_fields = BasePage.search_fields + [
        index.SearchField('introduction'),
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        subpages = ProjectPage.objects.descendant_of(self).live().public().select_related('icon').order_by('-first_published_at')
        per_page = settings.DEFAULT_PER_PAGE
        page_number = request.GET.get('page')
        paginator = Paginator(subpages, per_page)

        try:
            subpages = paginator.page(page_number)
        except PageNotAnInteger:
            subpages = paginator.page(1)
        except EmptyPage:
            subpages = paginator.page(paginator.num_pages)

        context['subpages'] = subpages

        return context
