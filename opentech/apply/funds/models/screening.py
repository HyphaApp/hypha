from django.db import models


# TODO: this should only be editable by admins
class ScreeningStatus(models.Model):
    title = models.CharField(max_length=128)

    class Meta:
        verbose_name_plural = "screening statuses"

    def __str__(self):
        return self.title
