from django.db import models

from modelcluster.fields import ParentalKey

from wagtail.wagtailcore.fields import RichTextField
from wagtail.wagtailadmin.edit_handlers import (
    FieldPanel, FieldRowPanel,
    MultiFieldPanel, InlinePanel
)
from wagtail.wagtailforms.models import AbstractFormField
from wagtail.wagtailsearch import index

from wagtailcaptcha.models import WagtailCaptchaEmailForm

from opentech.utils.models import BasePage


class FormField(AbstractFormField):
    page = ParentalKey('FormPage', related_name='form_fields')


class FormPage(WagtailCaptchaEmailForm, BasePage):
    subpage_types = []

    introduction = models.TextField(blank=True)
    thank_you_text = RichTextField(blank=True, help_text="Text displayed to the user on successful submission of the form")
    action_text = models.CharField(max_length=32, blank=True, help_text="Form action text. Defaults to \"Submit\"")

    search_fields = BasePage.search_fields + [
        index.SearchField('introduction'),
    ]

    content_panels = BasePage.content_panels + [
        FieldPanel('introduction'),
        InlinePanel('form_fields', label="Form fields"),
        FieldPanel('action_text'),
        FieldPanel('thank_you_text'),
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel('from_address', classname="col6"),
                FieldPanel('to_address', classname="col6"),
            ]),
            FieldPanel('subject'),
        ], "Email"),
    ]
