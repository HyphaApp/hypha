from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import models
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from pagedown.widgets import PagedownWidget
from wagtail.admin.panels import (
    FieldPanel,
    FieldRowPanel,
    InlinePanel,
    MultiFieldPanel,
    PageChooserPanel,
)
from wagtail.fields import StreamField
from wagtail.models import Orderable, PageManager
from wagtail.query import PageQuerySet
from wagtail.search import index

from hypha.public.utils.blocks import StoryBlock
from hypha.public.utils.models import BaseFunding, BasePage, FundingMixin, RelatedPage


class SocialMediaProfile(models.Model):
    person_page = ParentalKey(
        'PersonPage',
        related_name='social_media_profile'
    )
    site_titles = (
        ('twitter', "Twitter"),
        ('linkedin', "LinkedIn"),
    )
    site_urls = (
        ('twitter', 'https://twitter.com/'),
        ('linkedin', 'https://www.linkedin.com/in/')
    )
    service = models.CharField(
        max_length=200,
        choices=site_titles
    )
    username = models.CharField(max_length=255)

    @property
    def profile_url(self):
        return dict(self.site_urls)[self.service] + self.username

    def clean(self):
        if self.service == 'twitter' and self.username.startswith('@'):
            self.username = self.username[1:]


class PersonType(models.Model):
    title = models.CharField(max_length=255)

    def __str__(self):
        return self.title


class PersonPagePersonType(models.Model):
    page = ParentalKey('PersonPage', related_name='person_types')
    person_type = models.ForeignKey(
        'PersonType',
        related_name='+',
        on_delete=models.PROTECT,
    )

    panels = [
        FieldPanel('person_type')
    ]

    def __str__(self):
        return self.person_type.title


class FundingQuerySet(models.QuerySet):
    def people(self):
        return PersonPage.objects.filter(id__in=self.values_list('page__id')).live().active().public()


class Funding(BaseFunding):
    page = ParentalKey('PersonPage', related_name='funding')

    objects = FundingQuerySet.as_manager()


class PersonContactInfomation(Orderable):
    methods = (
        ('irc', 'IRC'),
        ('im', 'IM/Jabber/XMPP'),
        ('phone', 'Phone'),
        ('pgp', 'PGP fingerprint'),
        ('otr', 'OTR fingerprint'),
    )
    page = ParentalKey('PersonPage', related_name='contact_details')
    contact_method = models.CharField(max_length=255, choices=methods, blank=True)
    other_method = models.CharField(max_length=255, blank=True, verbose_name=_('Other'))
    contact_detail = models.CharField(max_length=255)

    panels = [
        FieldRowPanel([
            FieldPanel('contact_method'),
            FieldPanel('other_method'),
        ]),
        FieldPanel('contact_detail'),
    ]

    @property
    def method_display(self):
        return self.other_method or self.get_contact_method_display()

    def clean(self):
        if not (self.contact_method or self.other_method):
            raise ValidationError({
                'contact_method': 'Please select or type at least one contact method.',
                'other_method': '',
            })

        if self.contact_method and self.other_method:
            raise ValidationError({
                'contact_method': 'Please only select or type one contact method.',
                'other_method': '',
            })


class ReviewerQuerySet(models.QuerySet):
    def people(self):
        return PersonPage.objects.filter(id__in=self.values_list('reviewer__id')).live().active().public()


class FundReviewers(RelatedPage):
    page = models.ForeignKey('wagtailcore.Page', null=True, blank=True, on_delete=models.SET_NULL, related_name='reviewers')
    reviewer = ParentalKey('PersonPage', related_name='funds_reviewed')

    objects = ReviewerQuerySet.as_manager()

    panels = [
        PageChooserPanel('page', 'public_funds.FundPage'),
    ]


class PersonQuerySet(PageQuerySet):
    def active(self):
        return self.filter(active=True)


class PersonPage(FundingMixin, BasePage):
    subpage_types = []
    parent_page_types = ['PersonIndexPage']

    drupal_id = models.IntegerField(null=True, blank=True, editable=False)

    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255)
    photo = models.ForeignKey(
        'images.CustomImage',
        null=True,
        blank=True,
        related_name='+',
        on_delete=models.SET_NULL
    )
    active = models.BooleanField(default=True)
    job_title = models.CharField(max_length=255, blank=True)
    introduction = models.TextField(blank=True)
    website = models.URLField(blank=True, max_length=255)
    biography = StreamField(StoryBlock(), blank=True, use_json_field=True)
    email = models.EmailField(blank=True)

    objects = PageManager.from_queryset(PersonQuerySet)()

    search_fields = BasePage.search_fields + [
        index.SearchField('introduction'),
        index.SearchField('biography')
    ]

    content_panels = BasePage.content_panels + [
        MultiFieldPanel([
            FieldPanel('first_name'),
            FieldPanel('last_name'),
        ], heading=_('Name')),
        FieldPanel('active'),
        FieldPanel('photo'),
        FieldPanel('job_title'),
        InlinePanel('social_media_profile', label=_('Social accounts')),
        FieldPanel('website'),
        MultiFieldPanel([
            FieldPanel('email'),
            InlinePanel('contact_details', label=_('Other Contact Methods')),
        ], heading=_('Contact information')),
        InlinePanel('person_types', label=_('Person types')),
        FieldPanel('introduction'),
        FieldPanel('biography'),
        InlinePanel('funds_reviewed', label=_('Funds Reviewed')),
    ] + FundingMixin.content_panels


class PersonIndexPage(BasePage):
    subpage_types = ['PersonPage']
    parent_page_types = ['standardpages.IndexPage']

    introduction = models.TextField(blank=True)

    content_panels = BasePage.content_panels + [
        FieldPanel('introduction', widget=PagedownWidget()),
    ]

    search_fields = BasePage.search_fields + [
        index.SearchField('introduction'),
    ]

    def get_context(self, request, *args, **kwargs):
        people = PersonPage.objects.live().public().descendant_of(self).order_by(
            'title',
        ).select_related(
            'photo',
        ).prefetch_related(
            'person_types__person_type',
        )

        if request.GET.get('person_type') and request.GET.get('person_type').isdigit():
            people = people.filter(person_types__person_type=request.GET.get('person_type'))

        if not request.GET.get('include_inactive') == 'true':
            people = people.filter(active=True)

        page_number = request.GET.get('page')
        paginator = Paginator(people, settings.DEFAULT_PER_PAGE)
        try:
            people = paginator.page(page_number)
        except PageNotAnInteger:
            people = paginator.page(1)
        except EmptyPage:
            people = paginator.page(paginator.num_pages)

        context = super().get_context(request, *args, **kwargs)
        context.update(
            people=people,
            # Only show person types that have been used
            person_types=PersonPagePersonType.objects.all().values_list(
                'person_type__pk', 'person_type__title'
            ).distinct()
        )

        return context
