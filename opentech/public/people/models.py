from django.db import models
from django.core.exceptions import ValidationError
from django.utils.functional import cached_property
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.conf import settings

from modelcluster.fields import ParentalKey

from wagtail.wagtailcore.models import Orderable
from wagtail.wagtailcore.fields import StreamField
from wagtail.wagtailadmin.edit_handlers import (
    FieldPanel,
    FieldRowPanel,
    InlinePanel,
    MultiFieldPanel,
    StreamFieldPanel
)
from wagtail.wagtailimages.edit_handlers import ImageChooserPanel

from opentech.public.utils.blocks import StoryBlock
from opentech.public.utils.models import BasePage, BaseFunding, FundingMixin


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
        related_name='+'
    )

    panels = [
        FieldPanel('person_type')
    ]

    def __str__(self):
        return self.person_type.title


class Funding(BaseFunding):
    page = ParentalKey('PersonPage', related_name='funding')


class PersonContactInfomation(Orderable):
    methods = (
        ('irc', 'IRC'),
        ('im_jabber_xmpp', 'IM/Jabber/XMPP'),
        ('phone', 'Phone'),
        ('pgp', 'PGP fingerprint'),
        ('otr', 'OTR fingerprint'),
    )
    page = ParentalKey('PersonPage', related_name='contact_details')
    contact_method = models.CharField(max_length=255, choices=methods, blank=True)
    other_method = models.CharField(max_length=255, blank=True, verbose_name='Other')
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


class PersonPage(FundingMixin, BasePage):
    subpage_types = []
    parent_page_types = ['PersonIndexPage']

    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    photo = models.ForeignKey(
        'images.CustomImage',
        null=True,
        blank=True,
        related_name='+',
        on_delete=models.SET_NULL
    )
    job_title = models.CharField(max_length=255)
    introduction = models.TextField(blank=True)
    website = models.URLField(blank=True, max_length=255)
    biography = StreamField(StoryBlock(), blank=True)
    email = models.EmailField(blank=True)

    content_panels = BasePage.content_panels + [
        MultiFieldPanel([
            FieldPanel('first_name'),
            FieldPanel('last_name'),
        ], heading="Name"),
        ImageChooserPanel('photo'),
        FieldPanel('job_title'),
        InlinePanel('social_media_profile', label='Social accounts'),
        FieldPanel('website'),
        MultiFieldPanel([
            FieldPanel('email'),
            InlinePanel('contact_details', label='Other Contact Methods'),
        ], heading='Contact information'),
        InlinePanel('person_types', label='Person types'),
        FieldPanel('introduction'),
        StreamFieldPanel('biography'),
        InlinePanel('funding', label='Funding'),
    ]


class PersonIndexPage(BasePage):
    subpage_types = ['PersonPage']
    parent_page_types = ['home.HomePage']

    @cached_property
    def people(self):
        return self.get_children().specific().live().public()

    def get_context(self, request, *args, **kwargs):
        page_number = request.GET.get('page')
        paginator = Paginator(self.people, settings.DEFAULT_PER_PAGE)
        try:
            people = paginator.page(page_number)
        except PageNotAnInteger:
            people = paginator.page(1)
        except EmptyPage:
            people = paginator.page(paginator.num_pages)

        context = super().get_context(request, *args, **kwargs)
        context.update(people=people)

        return context
