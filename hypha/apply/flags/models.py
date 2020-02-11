from django.conf import settings
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class Flag(models.Model):
    STAFF = 'staff'
    USER = 'user'
    FLAG_TYPES = {
        STAFF: 'Staff',
        USER: 'User',
    }
    target_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    target_object_id = models.PositiveIntegerField()
    target = GenericForeignKey('target_content_type', 'target_object_id')
    timestamp = models.DateTimeField(auto_now_add=True)
    type = models.CharField(
        choices=FLAG_TYPES.items(),
        default='user',
        max_length=15,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
    )
