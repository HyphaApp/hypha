import datetime

from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.shortcuts import redirect

from pagedown.widgets import PagedownWidget

from wagtail.core.models import Page
from wagtail.core.fields import RichTextField
from wagtail.admin.edit_handlers import FieldPanel
from wagtail.search import index
from wagtail.images.edit_handlers import ImageChooserPanel

from hypha.public.utils.models import BasePage
from hypha.apply.funds.models import ApplicationSubmission


class PartnerIndexPage(BasePage):
    parent_page_types = ['standardpages.IndexPage']
    subpage_types = ['partner.PartnerPage']

    introduction = models.TextField(blank=True)

    content_panels = BasePage.content_panels + [
        FieldPanel('introduction', widget=PagedownWidget()),
    ]

    search_fields = BasePage.search_fields + [
        index.SearchField('introduction'),
    ]

    def serve(self, request, *args, **kwargs):
        # import ipdb; ipdb.set_trace()
        return redirect('investments')
        # return super().serve(request, *args, **kwargs)


class PartnerPage(BasePage):
    STATUS = [
        ('active', 'Active'),
        ('inactive', 'Inactive')
    ]

    class Meta:
        verbose_name = "Partner Page"

    parent_page_types = ['partner.PartnerIndexPage']
    subpage_types = []

    name = models.CharField(max_length=100)
    status = models.CharField(
        choices=STATUS, default='current_partner', max_length=20
    )
    public = models.BooleanField(default=True)
    description = RichTextField(blank=True)
    web_url = models.URLField(blank=True)
    logo = models.OneToOneField(
        'images.CustomImage',
        null=True,
        blank=True,
        related_name='+',
        on_delete=models.SET_NULL
    )

    content_panels = Page.content_panels + [
        FieldPanel('name'),
        FieldPanel('status'),
        FieldPanel('public'),
        FieldPanel('description'),
        FieldPanel('web_url'),
        ImageChooserPanel('logo'),
    ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return self.url


def current_year():
    return datetime.date.today().year


def max_value_current_year(value):
    return MaxValueValidator(current_year())(value)


class Investment(models.Model):

    partner = models.ForeignKey(
        PartnerPage,
        on_delete=models.CASCADE,
        related_name='investments'
    )
    name = models.CharField(max_length=50)
    year = models.IntegerField(
        default=current_year,
        validators=[MinValueValidator(1984), max_value_current_year],
        help_text='Use format: <YYYY>'
    )
    amount_committed = models.DecimalField(
        decimal_places=2,
        default=0,
        max_digits=11,
        verbose_name='Ammount Commited US$'
    )
    description = models.TextField()
    application = models.OneToOneField(
        ApplicationSubmission,
        on_delete=models.SET_NULL,
        blank=True, null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
