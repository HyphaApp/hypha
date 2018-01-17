from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.core.validators import URLValidator

from modelcluster.fields import ParentalKey
from wagtail.wagtailadmin.edit_handlers import (
    FieldPanel,
    InlinePanel,
    PageChooserPanel,
    StreamFieldPanel,
)

from wagtail.wagtailcore.fields import StreamField
from wagtail.wagtailimages.edit_handlers import ImageChooserPanel
from wagtail.wagtailsearch import index

from opentech.public.utils.blocks import StoryBlock
from opentech.public.utils.models import (
    BaseFunding,
    BasePage,
    FundingMixin,
    RelatedPage,
)


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


class ProjectFunding(BaseFunding):
    page = ParentalKey('ProjectPage', related_name='funding')


class ProjectPage(FundingMixin, BasePage):
    STATUSES = (
        ('idea', "Just an Idea (Pre-alpha)"),
        ('exists', "It Exists! (Alpha/Beta)"),
        ('release', "It's basically done. (Release)"),
        ('production', "People Use It. (Production)"),
    )

    subpage_types = []
    parent_page_types = ['ProjectIndexPage']

    introduction = models.TextField(blank=True)
    icon = models.ForeignKey(
        'images.CustomImage',
        null=True,
        blank=True,
        related_name='+',
        on_delete=models.SET_NULL
    )
    status = models.CharField(choices=STATUSES, max_length=25, default=STATUSES[0][0])
    body = StreamField(StoryBlock())

    search_fields = BasePage.search_fields + [
        index.SearchField('introduction'),
        index.SearchField('body'),
    ]

    content_panels = BasePage.content_panels + [
        ImageChooserPanel('icon'),
        FieldPanel('introduction'),
        FieldPanel('status'),
        StreamFieldPanel('body'),
        InlinePanel('contact_details', label="Contact Details"),
        InlinePanel('related_pages', label="Related pages"),
        InlinePanel('funding', label="Funding"),
    ]


class ProjectIndexPage(BasePage):
    subpage_types = ['ProjectPage']
    parent_page_types = ['home.Homepage']

    introduction = models.TextField(blank=True)

    content_panels = BasePage.content_panels + [
        FieldPanel('introduction'),
    ]

    search_fields = BasePage.search_fields + [
        index.SearchField('introduction'),
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        subpages = self.get_children().live()
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
