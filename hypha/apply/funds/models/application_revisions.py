from django.conf import settings
from django.db import models
from django.urls import reverse

from hypha.apply.stream_forms.files import StreamFieldDataEncoder
from hypha.apply.stream_forms.models import BaseStreamForm

from .mixins import AccessFormData


class ApplicationRevision(BaseStreamForm, AccessFormData, models.Model):
    wagtail_reference_index_ignore = True

    submission = models.ForeignKey(
        "funds.ApplicationSubmission",
        related_name="revisions",
        on_delete=models.CASCADE,
    )
    form_data = models.JSONField(encoder=StreamFieldDataEncoder)
    timestamp = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )

    # Is the revision a draft - also used by previews to save before rendering
    is_draft = models.BooleanField(default=False)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"Revision for {self.submission.title} by {self.author} "

    @property
    def form_fields(self):
        return self.submission.form_fields

    def get_compare_url_to_latest(self):
        return reverse(
            "funds:submissions:revisions:compare",
            kwargs={
                "submission_pk": self.submission.id,
                "to": self.submission.live_revision.id,
                "from": self.id,
            },
        )

    def get_absolute_url(self):
        # Compares against the previous revision
        previous_revision = self.submission.revisions.filter(id__lt=self.id).first()
        return reverse(
            "funds:submissions:revisions:compare",
            kwargs={
                "submission_pk": self.submission.id,
                "to": self.id,
                "from": previous_revision.id,
            },
        )
