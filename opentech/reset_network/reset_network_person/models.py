from django.db import models
from wagtail.admin.edit_handlers import FieldPanel, MultiFieldPanel
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.snippets.models import register_snippet


@register_snippet
class ResetNetworkPerson(models.Model):

    class Meta:
        verbose_name = "Reset Network Person"
        verbose_name_plural = "Reset Network People"

    def __str__(self):
        return self.name

    name = models.CharField(max_length=255, blank=False)
    role = models.CharField(max_length=255, blank=False)
    about = models.TextField()
    image = models.ForeignKey('images.CustomImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    linkedin = models.URLField()
    twitter = models.URLField()

    panels = [
        MultiFieldPanel([
            FieldPanel('name'),
            FieldPanel('role'),
            FieldPanel('about'),
            ImageChooserPanel('image'),
            FieldPanel('linkedin'),
            FieldPanel('twitter'),
        ], heading='Content'),
    ]
