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
    FIRST_STAGE = 1
    SECOND_STAGE = 2
    STAGE_CHOICES = [
        (FIRST_STAGE, '1st Stage'),
        (SECOND_STAGE, '2nd Stage'),
    ]
    form = models.ForeignKey('ApplicationForm', on_delete=models.PROTECT)
    stage = models.PositiveSmallIntegerField(choices=STAGE_CHOICES)

    panels = [
        FilteredFieldPanel('form', filter_query={'roundbaseform__isnull': True}),
        FieldPanel('stage'),
    ]

    @property
    def fields(self):
        return self.form.form_fields

    class Meta(Orderable.Meta):
        abstract = True

    def __eq__(self, other):
        try:
            return self.fields == other.fields and self.sort_order == other.sort_order
        except AttributeError:
            return False

    def __str__(self):
        return self.form.name


class ApplicationBaseForm(AbstractRelatedForm):
    application = ParentalKey('ApplicationBase', related_name='forms')


class RoundBaseForm(AbstractRelatedForm):
    round = ParentalKey('RoundBase', related_name='forms')


class LabBaseForm(AbstractRelatedForm):
    lab = ParentalKey('LabBase', related_name='forms')


class AbstractRelatedReviewForm(Orderable):
    class Meta(Orderable.Meta):
        abstract = True

    form = models.ForeignKey('review.ReviewForm', on_delete=models.PROTECT)

    panels = [
        FilteredFieldPanel('form', filter_query={
            'roundbasereviewform__isnull': True,
        })
    ]

    @property
    def fields(self):
        return self.form.form_fields

    def __eq__(self, other):
        try:
            return self.fields == other.fields and self.sort_order == other.sort_order
        except AttributeError:
            return False

    def __str__(self):
        return self.form.name


class ApplicationBaseReviewForm(AbstractRelatedReviewForm):
    application = ParentalKey('ApplicationBase', related_name='review_forms')


class RoundBaseReviewForm(AbstractRelatedReviewForm):
    round = ParentalKey('RoundBase', related_name='review_forms')


class LabBaseReviewForm(AbstractRelatedReviewForm):
    lab = ParentalKey('LabBase', related_name='review_forms')
