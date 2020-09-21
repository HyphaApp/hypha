from wagtail.contrib.settings.models import BaseSetting, register_setting
from hypha.apply.categories.models import Category

from django.db import models
from wagtail.admin.edit_handlers import FieldPanel


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
