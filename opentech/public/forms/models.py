import json

from django.core.serializers.json import DjangoJSONEncoder
from django.conf import settings
from django.db import models
from django.forms import FileField
from django.utils.translation import ugettext_lazy as _

from modelcluster.fields import ParentalKey

from wagtail.core.fields import RichTextField
from wagtail.admin.edit_handlers import (
    FieldPanel, FieldRowPanel, MultiFieldPanel, InlinePanel
)
from wagtail.contrib.forms.forms import FormBuilder
from wagtail.contrib.forms.models import (
    AbstractEmailForm, AbstractFormField, FORM_FIELD_CHOICES
)
from wagtail.documents.models import get_document_model
from wagtail.search import index

from opentech.public.utils.models import BasePage


def filename_to_title(filename):
    from os.path import splitext
    if filename:
        result = splitext(filename)[0]
        result = result.replace('-', ' ').replace('_', ' ')
        return result.title()


class FormField(AbstractFormField):
    FORM_FIELD_CHOICES = FORM_FIELD_CHOICES + (('document', 'Upload Document'),)
    field_type = models.CharField(
        verbose_name=_('field type'),
        max_length=16,
        choices=FORM_FIELD_CHOICES
    )
    page = ParentalKey('FormPage', on_delete=models.CASCADE, related_name='form_fields')


class ExtendedFormBuilder(FormBuilder):
    def create_document_field(self, field, options):
        return FileField(**options)


class FormPage(AbstractEmailForm, BasePage):
    form_builder = ExtendedFormBuilder
    subpage_types = []

    intro = RichTextField(blank=True)
    thank_you_text = RichTextField(blank=True)

    search_fields = BasePage.search_fields + [
        index.SearchField('intro'),
    ]

    content_panels = BasePage.content_panels + [
        FieldPanel('intro', classname="full"),
        InlinePanel('form_fields', label="Form fields"),
        FieldPanel('thank_you_text', classname="full"),
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel('from_address', classname="col6"),
                FieldPanel('to_address', classname="col6"),
            ]),
            FieldPanel('subject'),
        ], "Email"),
    ]

    def process_form_submission(self, form):
        cleaned_data = form.cleaned_data

        for name, field in form.fields.items():
            if isinstance(field, FileField):
                file_data = cleaned_data[name]
                if file_data:
                    DocumentModel = get_document_model()
                    if form.user.is_anonymous:
                        document = DocumentModel(
                            file=cleaned_data[name],
                            title=filename_to_title(cleaned_data[name].name),
                        )
                    else:
                        document = DocumentModel(
                            file=cleaned_data[name],
                            title=filename_to_title(cleaned_data[name].name),
                            uploaded_by_user=form.user,
                        )
                    document.save()
                    if settings.DEBUG:
                        file_details_dict = {name: 'localhost:8000' + document.url}
                    else:
                        file_details_dict = {name: 'https://www.opentech.fund' + document.url}
                    cleaned_data.update(file_details_dict)
                else:
                    del cleaned_data[name]

        form_data = json.dumps(cleaned_data, cls=DjangoJSONEncoder)
        return self.get_submission_class().objects.create(
            form_data=form_data,
            page=self,
        )
