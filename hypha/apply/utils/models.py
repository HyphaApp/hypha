from django.contrib.auth.models import Group
from django.db import models
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.contrib.settings.models import (
    BaseGenericSetting,
    BaseSiteSetting,
    register_setting,
)
from wagtail.models import Orderable


@register_setting
class PDFPageSettings(BaseSiteSetting):
    A4 = "A4"
    LEGAL = "legal"
    LETTER = "letter"
    PAGE_SIZES = [
        (A4, "A4"),
        (LEGAL, "Legal"),
        (LETTER, "Letter"),
    ]

    class Meta:
        verbose_name = "pdf settings"

    download_page_size = models.CharField(
        choices=PAGE_SIZES,
        default=LEGAL,
        max_length=6,
        help_text=_("Page size of downloadable Project and Submission PDFs"),
    )

    panels = [
        FieldPanel("download_page_size"),
    ]


@register_setting
class SubmissionsDetailsSetting(BaseGenericSetting, ClusterableModel):
    """Allows settings per Group to be specified in Wagtail Settings and retrieved by the Submissions Details code.
    This class affords a setting for a single Site to be referenced by the SubmissionsDetailsSettings model. This way
    the BaseSetting can be extended such that a setting appears in the Wagtail Settings menu but there can also be up to
    one row per group for settings."""

    class Meta:
        verbose_name = "Submissions Details Page Setting"

    panels = [InlinePanel("submissions_details_settings")]


class SubmissionsDetailsSettings(Orderable):
    class Meta:
        verbose_name = "Submissions Details Page Settings"
        constraints = [
            # There is a one-to-one relation for setting-to-site. Therefore, "setting" can be thought of as "site" here.
            models.UniqueConstraint(
                fields=["setting", "group"], name="unique_site_group"
            ),
        ]

    setting = ParentalKey(
        to=SubmissionsDetailsSetting,
        on_delete=models.CASCADE,
        related_name="submissions_details_settings",
    )
    group = models.ForeignKey(
        to=Group,
        on_delete=models.CASCADE,
    )

    # The actual settings that can apply to a given site/group combination follow.
    sees_related_submissions = models.BooleanField(
        default=False,
        help_text=_(
            "Should members of the above Group see the related submissions side panel when reviewing a submission?"
        ),
    )

    panels = [
        FieldPanel("group"),
        FieldPanel("sees_related_submissions"),
    ]
