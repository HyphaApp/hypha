import json
import os

from django.conf import settings
from django.core.files.storage import get_storage_class
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.forms import FileField, FileInput
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from modelcluster.fields import ParentalKey
from wagtail.admin.edit_handlers import (
    FieldPanel,
    FieldRowPanel,
    InlinePanel,
    MultiFieldPanel,
)
from wagtail.contrib.forms.forms import FormBuilder
from wagtail.contrib.forms.models import (
    FORM_FIELD_CHOICES,
    AbstractEmailForm,
    AbstractFormField,
)
from wagtail.core.fields import RichTextField
from wagtail.search import index

from hypha.public.utils.models import BasePage

webform_storage = get_storage_class(getattr(settings, 'PRIVATE_FILE_STORAGE', None))()


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
        return FileField(widget=FileInput(attrs={'accept': settings.FILE_ALLOWED_EXTENSIONS}), **options)


@method_decorator(never_cache, name='serve')
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
        InlinePanel('form_fields', label=_('Form fields')),
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
                    file_name = file_data.name
                    file_name = webform_storage.generate_filename(file_name)
                    upload_to = os.path.join('webform', str(self.id), file_name)
                    saved_file_name = webform_storage.save(upload_to, file_data)
                    file_details_dict = {name: webform_storage.url(saved_file_name)}
                    cleaned_data.update(file_details_dict)
                else:
                    del cleaned_data[name]

        form_data = json.dumps(cleaned_data, cls=DjangoJSONEncoder)
        return self.get_submission_class().objects.create(
            form_data=form_data,
            page=self,
        )
