from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy


class Flag(models.Model):
    STAFF = "staff"
    USER = "user"
    FLAG_TYPES = {
        STAFF: _("Staff"),
        USER: _("User"),
    }
    target_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    target_object_id = models.PositiveIntegerField()
    target = GenericForeignKey("target_content_type", "target_object_id")
    timestamp = models.DateTimeField(auto_now_add=True)
    type = models.CharField(
        choices=FLAG_TYPES.items(),
        default="user",
        max_length=15,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
    )

    class Meta:
        verbose_name = pgettext_lazy("computing", "flag")
        verbose_name_plural = pgettext_lazy("computing", "flags")
