from django.db import models

from modelcluster.fields import ParentalKey

from wagtail.admin.edit_handlers import (
    FieldPanel,
    StreamFieldPanel,
)
from wagtail.core.fields import StreamField
from wagtail.core.models import Orderable

from ..blocks import ApplicationCustomFormFieldsBlock
from ..edit_handlers import FilteredFieldPanel


class ApplicationForm(models.Model):
    name = models.CharField(max_length=255)
    form_fields = StreamField(ApplicationCustomFormFieldsBlock())

    panels = [
        FieldPanel('name'),
        StreamFieldPanel('form_fields'),
    ]

    def __str__(self):
        return self.name


class AbstractRelatedForm(Orderable):
    form = models.ForeignKey('ApplicationForm', on_delete=models.PROTECT)

    panels = [
        FilteredFieldPanel('form', filter_query={'roundform__isnull': True})
    ]

    @property
    def fields(self):
        return self.form.form_fields

    class Meta(Orderable.Meta):
        abstract = True

    def __eq__(self, other):
        try:
            return self.fields == other.fields
        except AttributeError:
            return False

    def __str__(self):
        return self.form.name


class ApplicationBaseForm(AbstractRelatedForm):
    application = ParentalKey('ApplicationBase', related_name='forms')


class RoundBaseForm(AbstractRelatedForm):
    round = ParentalKey('RoundBase', related_name='forms')


class AbstractRelatedReviewForm(Orderable):
    form = models.ForeignKey('review.ReviewForm', on_delete=models.PROTECT)

    panels = [
        FieldPanel('form')
    ]

    @property
    def fields(self):
        return self.form.form_fields

    class Meta(Orderable.Meta):
        abstract = True

    def __eq__(self, other):
        try:
            return self.fields == other.fields
        except AttributeError:
            return False

    def __str__(self):
        return self.form.name


class ApplicationBaseReviewForm(AbstractRelatedReviewForm):
    fund = ParentalKey('ApplicationBase', related_name='review_forms')


class LabBaseForm(AbstractRelatedForm):
    lab = ParentalKey('LabBase', related_name='forms')


class LabBaseReviewForm(AbstractRelatedReviewForm):
    lab = ParentalKey('LabBase', related_name='review_forms')
