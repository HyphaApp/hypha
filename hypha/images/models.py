from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.images.models import AbstractImage, AbstractRendition, Image


class CustomImage(AbstractImage):
    """
    Custom image class to replace wagtailimages.Image, providing various
    additional data fields
    """

    alt = models.CharField(max_length=255, blank=True)
    credit = models.CharField(max_length=255, blank=True)

    admin_form_fields = Image.admin_form_fields + (
        "alt",
        "credit",
    )

    class Meta:
        verbose_name = _("custom image")
        verbose_name_plural = _("custom images")

    # When you save the image, check if alt text has been set. If not, set it as the title.
    def save(self, *args, **kwargs):
        if not self.alt:
            self.alt = self.title

        super().save(*args, **kwargs)


class Rendition(AbstractRendition):
    image = models.ForeignKey(
        "CustomImage", related_name="renditions", on_delete=models.CASCADE
    )

    class Meta:
        unique_together = (("image", "filter_spec", "focal_point_key"),)
        verbose_name = _("rendition")
        verbose_name_plural = _("renditions")
