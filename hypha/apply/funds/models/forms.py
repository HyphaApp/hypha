from django.db import models
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel
from wagtail.fields import StreamField
from wagtail.models import Orderable

from ...projects.models.project import ProjectReportForm
from ..blocks import ApplicationCustomFormFieldsBlock
from ..edit_handlers import FilteredFieldPanel


class ApplicationForm(models.Model):
    wagtail_reference_index_ignore = True

    name = models.CharField(max_length=255)
    form_fields = StreamField(ApplicationCustomFormFieldsBlock())

    panels = [
        FieldPanel("name"),
        FieldPanel("form_fields"),
    ]

    class Meta:
        verbose_name = _("application form")
        verbose_name_plural = _("applications forms")

    def __str__(self):
        return self.name


class AbstractRelatedForm(Orderable):
    FIRST_STAGE = 1
    SECOND_STAGE = 2
    STAGE_CHOICES = [
        (FIRST_STAGE, _("1st Stage")),
        (SECOND_STAGE, _("2nd Stage")),
    ]
    form = models.ForeignKey("ApplicationForm", on_delete=models.PROTECT)
    stage = models.PositiveSmallIntegerField(choices=STAGE_CHOICES)

    panels = [
        FilteredFieldPanel("form", filter_query={"roundbaseform__isnull": True}),
        FieldPanel("stage"),
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
                if hasattr(other, "pk") and hasattr(self, "pk"):
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
    application = ParentalKey("ApplicationBase", related_name="forms")

    class Meta:
        verbose_name = _("application base form")
        verbose_name_plural = _("application base forms")


class RoundBaseForm(AbstractRelatedForm):
    round = ParentalKey("RoundBase", related_name="forms")

    class Meta:
        verbose_name = _("round base form")
        verbose_name_plural = _("round base forms")


class LabBaseForm(AbstractRelatedForm):
    lab = ParentalKey("LabBase", related_name="forms")

    class Meta:
        verbose_name = _("lab base form")
        verbose_name_plural = _("lab base forms")


class AbstractRelatedDeterminationForm(Orderable):
    class Meta(Orderable.Meta):
        abstract = True

    form = models.ForeignKey(
        "determinations.DeterminationForm", on_delete=models.PROTECT
    )

    panels = [
        FilteredFieldPanel(
            "form",
            filter_query={
                "roundbasedeterminationform__isnull": True,
            },
        )
    ]

    @property
    def fields(self):
        return self.form.form_fields

    def __eq__(self, other):
        try:
            if self.fields == other.fields and self.sort_order == other.sort_order:
                # If the objects are saved to db. pk should also be compared
                if hasattr(other, "pk") and hasattr(self, "pk"):
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

    form = models.ForeignKey("review.ReviewForm", on_delete=models.PROTECT)

    panels = [
        FilteredFieldPanel(
            "form",
            filter_query={
                "roundbasereviewform__isnull": True,
            },
        )
    ]

    @property
    def fields(self):
        return self.form.form_fields

    def __eq__(self, other):
        try:
            if self.fields == other.fields and self.sort_order == other.sort_order:
                # If the objects are saved to db. pk should also be compared
                if hasattr(other, "pk") and hasattr(self, "pk"):
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
    application = ParentalKey("ApplicationBase", related_name="review_forms")

    class Meta:
        verbose_name = _("application base review form")
        verbose_name_plural = _("application base review forms")


class ApplicationBaseExternalReviewForm(AbstractRelatedReviewForm):
    application = ParentalKey("ApplicationBase", related_name="external_review_forms")

    class Meta:
        verbose_name = _("application base external review form")
        verbose_name_plural = _("application base external review form")


class RoundBaseReviewForm(AbstractRelatedReviewForm):
    round = ParentalKey("RoundBase", related_name="review_forms")

    class Meta:
        verbose_name = _("round base review form")
        verbose_name_plural = _("round base review forms")


class RoundBaseExternalReviewForm(AbstractRelatedReviewForm):
    round = ParentalKey("RoundBase", related_name="external_review_forms")

    class Meta:
        verbose_name = _("round base externa review form")
        verbose_name_plural = _("round base external review forms")


class LabBaseReviewForm(AbstractRelatedReviewForm):
    lab = ParentalKey("LabBase", related_name="review_forms")

    class Meta:
        verbose_name = _("lab base review form")
        verbose_name_plural = _("lab base review forms")


class LabBaseExternalReviewForm(AbstractRelatedReviewForm):
    lab = ParentalKey("LabBase", related_name="external_review_forms")

    class Meta:
        verbose_name = _("lab base external review form")
        verbose_name_plural = _("lab base external review forms")


class ApplicationBaseDeterminationForm(AbstractRelatedDeterminationForm):
    application = ParentalKey("ApplicationBase", related_name="determination_forms")

    class Meta:
        verbose_name = _("application base determination form")
        verbose_name_plural = _("application base determination forms")


class RoundBaseDeterminationForm(AbstractRelatedDeterminationForm):
    round = ParentalKey("RoundBase", related_name="determination_forms")

    class Meta:
        verbose_name = _("round base determination form")
        verbose_name_plural = _("round base determination forms")


class LabBaseDeterminationForm(AbstractRelatedDeterminationForm):
    lab = ParentalKey("LabBase", related_name="determination_forms")

    class Meta:
        verbose_name = _("lab base determination form")
        verbose_name_plural = _("lab base determination forms")


class AbstractRelatedProjectForm(Orderable):
    class Meta(Orderable.Meta):
        abstract = True

    form = models.ForeignKey(
        "application_projects.ProjectForm", on_delete=models.PROTECT
    )

    @property
    def fields(self):
        return self.form.form_fields

    def __eq__(self, other):
        try:
            if self.fields == other.fields and self.sort_order == other.sort_order:
                # If the objects are saved to db. pk should also be compared
                if hasattr(other, "pk") and hasattr(self, "pk"):
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


class AbstractRelatedProjectSOWForm(Orderable):
    """Abstract class for SOW Form to use it in Funds and Labs, similar to the other forms liks ReviewForms etc"""

    class Meta(Orderable.Meta):
        abstract = True

    form = models.ForeignKey(
        "application_projects.ProjectSOWForm", on_delete=models.PROTECT
    )

    @property
    def fields(self):
        return self.form.form_fields

    def __eq__(self, other):
        try:
            if self.fields == other.fields and self.sort_order == other.sort_order:
                # If the objects are saved to db. pk should also be compared
                if hasattr(other, "pk") and hasattr(self, "pk"):
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


class ApplicationBaseProjectForm(AbstractRelatedProjectForm):
    application = ParentalKey("ApplicationBase", related_name="approval_forms")

    class Meta:
        verbose_name = _("application base project form")
        verbose_name_plural = _("application base project forms")


class ApplicationBaseProjectSOWForm(AbstractRelatedProjectSOWForm):
    application = ParentalKey("ApplicationBase", related_name="sow_forms")

    class Meta:
        verbose_name = _("application base project SOW form")
        verbose_name_plural = _("application base project SOW forms")


class LabBaseProjectForm(AbstractRelatedProjectForm):
    lab = ParentalKey("LabBase", related_name="approval_forms")

    class Meta:
        verbose_name = _("lab base project form")
        verbose_name_plural = _("lab base project forms")


class LabBaseProjectSOWForm(AbstractRelatedProjectSOWForm):
    lab = ParentalKey("LabBase", related_name="sow_forms")

    class Meta:
        verbose_name = _("lab base project SOW form")
        verbose_name_plural = _("lab base project SOW forms")


class AbstractRelatedProjectReportForm(Orderable):
    class Meta(Orderable.Meta):
        abstract = True

    form = models.ForeignKey(to=ProjectReportForm, on_delete=models.PROTECT)

    @property
    def fields(self):
        return self.form.form_fields

    def __eq__(self, other):
        try:
            if self.fields == other.fields and self.sort_order == other.sort_order:
                # If the objects are saved to db. pk should also be compared
                if hasattr(other, "pk") and hasattr(self, "pk"):
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


class ApplicationBaseProjectReportForm(AbstractRelatedProjectReportForm):
    application = ParentalKey("ApplicationBase", related_name="report_forms")

    class Meta:
        verbose_name = _("application base project report form")
        verbose_name_plural = _("application base project report forms")


class LabBaseProjectReportForm(AbstractRelatedProjectReportForm):
    lab = ParentalKey("LabBase", related_name="report_forms")

    class Meta:
        verbose_name = _("lab base project report form")
        verbose_name_plural = _("lab base project report forms")
