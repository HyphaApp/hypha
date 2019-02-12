from django.db import models
from wagtail.admin.edit_handlers import FieldPanel
from wagtail.images.edit_handlers import ImageChooserPanel


class ReviewerRole(models.Model):
    name = models.CharField(max_length=128)
    icon = models.ForeignKey(
        'images.CustomImage',
        null=True,
        blank=True,
        related_name='+',
        on_delete=models.SET_NULL
    )
    order = models.IntegerField(
        help_text='The order this role should appear in the Update Reviewers form.',
        null=True,
        blank=True,
    )

    panels = [
        FieldPanel('name'),
        ImageChooserPanel('icon'),
        FieldPanel('order'),
    ]

    def __str__(self):
        return self.name


