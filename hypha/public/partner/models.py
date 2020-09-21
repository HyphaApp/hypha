import datetime

from django import forms
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.shortcuts import redirect
from pagedown.widgets import PagedownWidget
from wagtail.admin.edit_handlers import FieldPanel
from wagtail.admin.forms import WagtailAdminModelForm
from wagtail.contrib.settings.models import BaseSetting, register_setting
from wagtail.core.fields import RichTextField
from wagtail.core.models import Page
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.search import index

from hypha.apply.categories.models import Category, Option
from hypha.apply.funds.models import ApplicationSubmission
from hypha.public.utils.models import BasePage


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
        return redirect('investments')


class PartnerPage(BasePage):
    STATUS = [
        ('active', 'Active'),
        ('inactive', 'Inactive')
    ]

    class Meta:
        verbose_name = "Partner Page"

    parent_page_types = ['partner.PartnerIndexPage']
    subpage_types = []

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
        FieldPanel('status'),
        FieldPanel('public'),
        FieldPanel('description'),
        FieldPanel('web_url'),
        ImageChooserPanel('logo'),
    ]

    def __str__(self):
        return self.title

    def get_context(self, request):
        context = super(PartnerPage, self).get_context(request)
        context['total_investments'] = sum(
            investment.amount_committed for investment in self.investments.all()
        )
        return context

    def get_absolute_url(self):
        return self.url


def current_year():
    return datetime.date.today().year


def max_value_current_year(value):
    return MaxValueValidator(current_year())(value)


@register_setting
class InvestmentCategorySettings(BaseSetting):
    class Meta:
        verbose_name = 'Investment Category Settings'

    categories = models.ManyToManyField(
        Category,
        help_text='Select the categories that should be used in investments.'
    )

    panels = [
        FieldPanel('categories'),
    ]


class InvestmentCategory(models.Model):
    investment = models.ForeignKey(
        'Investment', on_delete=models.CASCADE,
        related_name='categories'
    )
    name = models.CharField(max_length=255, null=True, blank=True)
    value = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.investment}: {self.name}: {self.value}"


class InvestmentAdminForm(WagtailAdminModelForm):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        ics = InvestmentCategorySettings.for_request(self.request)
        self.categories = ics.categories.all()
        for category in self.categories:
            field_name = category.name.lower().replace(' ', '_')
            self.fields[field_name] = forms.ModelChoiceField(
                required=False,
                queryset=category.options.all(),
            )
            if self.instance.name:
                try:
                    ic = InvestmentCategory.objects.get(
                        investment=self.instance,
                        name=category.name
                    )
                except InvestmentCategory.DoesNotExist:
                    pass
                else:
                    self.initial[field_name] = Option.objects.get(
                        value=ic.value
                    )

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data

    def save(self, commit=True):
        investment = super().save(commit)
        for category in self.categories:
            field_name = category.name.lower().replace(' ', '_')
            value = self.cleaned_data[field_name].value
            ic, _ = InvestmentCategory.objects.get_or_create(
                investment=investment,
                name=category.name
            )
            ic.value = value
            ic.save()
        return investment


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
    updated_at = models.DateTimeField(auto_now=True)

    base_form_class = InvestmentAdminForm

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for category in self.categories.all():
            field_name = category.name.lower().replace(' ', '_')
            setattr(self, field_name, category.value)

    def __str__(self):
        return self.name
