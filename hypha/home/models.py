from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.models import Page


class ApplyHomePage(Page):
    # Only allow creating HomePages at the root level
    parent_page_types = ["wagtailcore.Page"]
    subpage_types = ["funds.FundType", "funds.LabType", "funds.RequestForPartners"]

    strapline = models.CharField(blank=True, max_length=255)

    class Meta:
        verbose_name = _("Apply home page")
        verbose_name_plural = _("Apply home page")
