from django.conf import settings
from django.core import validators
from django.core.exceptions import ValidationError
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import models
from django.utils.deconstruct import deconstructible
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
from wagtail.search import index

from hypha.apply.funds.models import ApplicationSubmission
from hypha.apply.funds.workflow import OPEN_CALL_PHASES
from hypha.public.utils.models import BasePage, RelatedPage

from .blocks import FundBlock, LabBlock


class BaseApplicationRelatedPage(RelatedPage):
    source_page = ParentalKey('BaseApplicationPage', related_name='related_pages')


class BaseApplicationPage(BasePage):
    subpage_types = []
    parent_page_types = []

    application_type_model = ''

    introduction = models.TextField(blank=True)
    application_type = models.ForeignKey(
        'wagtailcore.Page',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='application_public',
    )
    body = StreamField(FundBlock(), use_json_field=True)

    search_fields = BasePage.search_fields + [
        index.SearchField('introduction'),
        index.SearchField('body')
    ]

    content_panels = BasePage.content_panels + [
        FieldPanel('introduction', widget=PagedownWidget()),
        FieldPanel('body'),
        InlinePanel('related_pages', label=_('Related pages')),
    ]

    def get_template(self, request, *args, **kwargs):
        # Make sure all children use the shared template
        return 'public_funds/fund_page.html'

    can_open = True

    @property
    def is_open(self):
        return self.application_type and bool(self.application_type.specific.open_round)

    @property
    def deadline(self):
        return self.application_type and self.application_type.specific.next_deadline()


class FundPage(BaseApplicationPage):
    parent_page_types = ['FundIndex']
    content_panels = BaseApplicationPage.content_panels[:]
    content_panels.insert(-2, PageChooserPanel('application_type', 'funds.FundType'))


class RFPPage(BaseApplicationPage):
    parent_page_types = ['LabPage']
    content_panels = BaseApplicationPage.content_panels[:]
    content_panels.insert(-2, PageChooserPanel('application_type', 'funds.RequestForPartners'))


class FundIndex(BasePage):
    subpage_types = ['FundPage']
    parent_page_types = ['home.HomePage']

    introduction = models.TextField(blank=True)

    content_panels = BasePage.content_panels + [
        FieldPanel('introduction', widget=PagedownWidget())
    ]

    def get_context(self, request, *args, **kwargs):
        funds = FundPage.objects.live().public().descendant_of(self)

        # Pagination
        page = request.GET.get('page', 1)
        paginator = Paginator(funds, settings.DEFAULT_PER_PAGE)
        try:
            funds = paginator.page(page)
        except PageNotAnInteger:
            funds = paginator.page(1)
        except EmptyPage:
            funds = paginator.page(paginator.num_pages)

        context = super().get_context(request, *args, **kwargs)
        context.update(subpages=funds)
        return context


class LabPageRelatedPage(RelatedPage):
    source_page = ParentalKey('LabPage', related_name='related_pages')


@deconstructible
class MailToAndURLValidator:
    email_validator = validators.EmailValidator()
    url_validator = validators.URLValidator()

    def __call__(self, value):
        if value.startswith('mailto://'):
            mail_to, email = value.rsplit('://', 1)
            self.email_validator(email)
        else:
            self.url_validator(value)


class LabPage(BasePage):
    subpage_types = ['RFPPage']
    parent_page_types = ['LabIndex']

    introduction = models.TextField(blank=True)
    icon = models.ForeignKey(
        'images.CustomImage',
        null=True,
        blank=True,
        related_name='+',
        on_delete=models.SET_NULL
    )
    lab_type = models.ForeignKey(
        'wagtailcore.Page',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='lab_public',
    )
    lab_link = models.CharField(blank=True, max_length=255, verbose_name=_('External link'), validators=[MailToAndURLValidator()])
    link_text = models.CharField(max_length=255, help_text=_('Text to display on the button for external links'), blank=True)
    body = StreamField(LabBlock(), use_json_field=True)

    search_fields = BasePage.search_fields + [
        index.SearchField('introduction'),
        index.SearchField('body')
    ]

    content_panels = BasePage.content_panels + [
        FieldPanel('icon'),
        FieldPanel('introduction'),
        MultiFieldPanel([
            PageChooserPanel('lab_type', 'funds.LabType'),
            FieldRowPanel([
                FieldPanel('lab_link'),
                FieldPanel('link_text'),
            ]),
        ], heading=_('Link for lab application')),
        FieldPanel('body'),
        InlinePanel('related_pages', label=_('Related pages')),
    ]

    def get_context(self, request):
        context = super().get_context(request)
        context['rfps'] = self.get_children().live().public()
        return context

    can_open = True

    @property
    def is_open(self):
        try:
            return bool(self.lab_type.specific.open_round)
        except AttributeError:
            return bool(self.lab_link)

    def clean(self):
        if self.lab_type and self.lab_link:
            raise ValidationError({
                'lab_type': _('Cannot link to both a Lab page and external link'),
                'lab_link': _('Cannot link to both a Lab page and external link'),
            })

        if not self.lab_type and not self.lab_link:
            raise ValidationError({
                'lab_type': _('Please provide a way for applicants to apply'),
                'lab_link': _('Please provide a way for applicants to apply'),
            })

        if self.lab_type and self.link_text:
            raise ValidationError({
                'link_text': _('Cannot customise the text for internal lab pages, leave blank'),
            })

        if self.lab_link and not self.link_text:
            raise ValidationError({
                'link_text': _('Please provide some text for the link button'),
            })


class LabIndex(BasePage):
    subpage_types = ['LabPage']
    parent_page_types = ['home.HomePage']

    introduction = models.TextField(blank=True)

    content_panels = BasePage.content_panels + [
        FieldPanel('introduction', widget=PagedownWidget())
    ]

    def get_context(self, request, *args, **kwargs):
        labs = LabPage.objects.live().public().descendant_of(self)

        # Pagination
        page = request.GET.get('page', 1)
        paginator = Paginator(labs, settings.DEFAULT_PER_PAGE)
        try:
            labs = paginator.page(page)
        except PageNotAnInteger:
            labs = paginator.page(1)
        except EmptyPage:
            labs = paginator.page(paginator.num_pages)

        context = super().get_context(request, *args, **kwargs)
        context.update(subpages=labs)
        return context


class OpenCallIndexPage(BasePage):
    subpage_types = []
    parent_page_types = ['home.HomePage']

    introduction = models.TextField(blank=True)

    content_panels = BasePage.content_panels + [
        FieldPanel('introduction'),
    ]

    search_fields = BasePage.search_fields + [
        index.SearchField('introduction'),
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        open_call_submissions = ApplicationSubmission.objects.filter(
            status__in=OPEN_CALL_PHASES).select_related('page').order_by('-submit_time')
        per_page = settings.DEFAULT_PER_PAGE
        page_number = request.GET.get('page')
        paginator = Paginator(open_call_submissions, per_page)

        try:
            open_call_submissions = paginator.page(page_number)
        except PageNotAnInteger:
            open_call_submissions = paginator.page(1)
        except EmptyPage:
            open_call_submissions = paginator.page(paginator.num_pages)

        context['open_call_submissions'] = open_call_submissions

        return context
