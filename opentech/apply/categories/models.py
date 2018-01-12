from django.db import models
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.wagtailadmin.edit_handlers import (
    FieldPanel,
    InlinePanel,
)
from wagtail.wagtailcore.models import Orderable


class Option(Orderable):
    value = models.CharField(max_length=255)
    category = ParentalKey('Category', related_name='options')


class Category(ClusterableModel):
    """Used to manage the global select questions used in most of the application form
    Also used in the front end by editors when writing about projects.

    When used in a form: name -> field label and help_text -> help_text
    """
    name = models.CharField(max_length=255)
    help_text = models.CharField(max_length=255, blank=True)

    panels = [
        FieldPanel('name'),
        FieldPanel('help_text'),
        InlinePanel('options', label='Options'),
    ]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Categories'
