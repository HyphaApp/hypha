from django.db import models
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel
from wagtail.fields import StreamField
from wagtail.models import Orderable

from ..blocks import ApplicationCustomFormFieldsBlock
from ..edit_handlers import FilteredFieldPanel


class ApplicationForm(models.Model):
    name = models.CharField(max_length=255)
    form_fields = StreamField(ApplicationCustomFormFieldsBlock(), use_json_field=True)

    panels = [
        FieldPanel('name'),
        FieldPanel('form_fields'),
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
            if self.fields == other.fields and self.sort_order == other.sort_order:
                # If the objects are saved to db. pk should also be compared
                if hasattr(other, 'pk') and hasattr(self, 'pk'):
                    return self.pk == other.pk
                return True
            return False
        except AttributeError:
            return False

    def __hash__(self):
        fields = [field.id for field in self.fields]
        return hash((tuple(fields), self.sort_order, self.pk))

    def __str__(self):
        return self.form.name


class ApplicationBaseForm(AbstractRelatedForm):
    application = ParentalKey('ApplicationBase', related_name='forms')


class RoundBaseForm(AbstractRelatedForm):
    round = ParentalKey('RoundBase', related_name='forms')


class LabBaseForm(AbstractRelatedForm):
    lab = ParentalKey('LabBase', related_name='forms')


class AbstractRelatedDeterminationForm(Orderable):
    class Meta(Orderable.Meta):
        abstract = True

    form = models.ForeignKey(
        'determinations.DeterminationForm', on_delete=models.PROTECT
    )

    panels = [
        FilteredFieldPanel('form', filter_query={
            'roundbasedeterminationform__isnull': True,
        })
    ]

    @property
    def fields(self):
        return self.form.form_fields

    def __eq__(self, other):
        try:
            if self.fields == other.fields and self.sort_order == other.sort_order:
                # If the objects are saved to db. pk should also be compared
                if hasattr(other, 'pk') and hasattr(self, 'pk'):
                    return self.pk == other.pk
                return True
            return False
        except AttributeError:
            return False

    def __hash__(self):
        fields = [field.id for field in self.fields]
        return hash((tuple(fields), self.sort_order, self.pk))

    def __str__(self):
        return self.form.name


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
            if self.fields == other.fields and self.sort_order == other.sort_order:
                # If the objects are saved to db. pk should also be compared
                if hasattr(other, 'pk') and hasattr(self, 'pk'):
                    return self.pk == other.pk
                return True
            return False
        except AttributeError:
            return False

    def __hash__(self):
        fields = [field.id for field in self.fields]
        return hash((tuple(fields), self.sort_order, self.pk))

    def __str__(self):
        return self.form.name


class ApplicationBaseReviewForm(AbstractRelatedReviewForm):
    application = ParentalKey('ApplicationBase', related_name='review_forms')


class ApplicationBaseExternalReviewForm(AbstractRelatedReviewForm):
    application = ParentalKey('ApplicationBase', related_name='external_review_forms')


class RoundBaseReviewForm(AbstractRelatedReviewForm):
    round = ParentalKey('RoundBase', related_name='review_forms')


class RoundBaseExternalReviewForm(AbstractRelatedReviewForm):
    round = ParentalKey('RoundBase', related_name='external_review_forms')


class LabBaseReviewForm(AbstractRelatedReviewForm):
    lab = ParentalKey('LabBase', related_name='review_forms')


class LabBaseExternalReviewForm(AbstractRelatedReviewForm):
    lab = ParentalKey('LabBase', related_name='external_review_forms')


class ApplicationBaseDeterminationForm(AbstractRelatedDeterminationForm):
    application = ParentalKey('ApplicationBase', related_name='determination_forms')


class RoundBaseDeterminationForm(AbstractRelatedDeterminationForm):
    round = ParentalKey('RoundBase', related_name='determination_forms')


class LabBaseDeterminationForm(AbstractRelatedDeterminationForm):
    lab = ParentalKey('LabBase', related_name='determination_forms')


class AbstractRelatedProjectApprovalForm(Orderable):
    class Meta(Orderable.Meta):
        abstract = True

    form = models.ForeignKey('application_projects.ProjectApprovalForm', on_delete=models.PROTECT)

    @property
    def fields(self):
        return self.form.form_fields

    def __eq__(self, other):
        try:
            if self.fields == other.fields and self.sort_order == other.sort_order:
                # If the objects are saved to db. pk should also be compared
                if hasattr(other, 'pk') and hasattr(self, 'pk'):
                    return self.pk == other.pk
                return True
            return False
        except AttributeError:
            return False

    def __hash__(self):
        fields = [field.id for field in self.fields]
        return hash((tuple(fields), self.sort_order, self.pk))

    def __str__(self):
        return self.form.name


class ApplicationBaseProjectApprovalForm(AbstractRelatedProjectApprovalForm):
    application = ParentalKey('ApplicationBase', related_name='approval_forms')


class LabBaseProjectApprovalForm(AbstractRelatedProjectApprovalForm):
    lab = ParentalKey('LabBase', related_name='approval_forms')
