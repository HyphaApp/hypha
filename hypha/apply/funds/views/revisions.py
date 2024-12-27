from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import (
    DetailView,
    ListView,
)

from hypha.apply.users.decorators import (
    staff_required,
)

from ..differ import compare
from ..models import (
    ApplicationRevision,
    ApplicationSubmission,
)


@method_decorator(staff_required, name="dispatch")
class RevisionListView(ListView):
    model = ApplicationRevision

    def get_queryset(self):
        """Get a queryset of all valid `ApplicationRevision`s that can be
        compared for the current submission

        This excludes draft & preview revisions unless draft(s) are the only
        existing revisions, in which the last draft will be returned in a QuerySet

        Returns:
            An [`ApplicationRevision`][hypha.apply.funds.models.ApplicationRevision] QuerySet
        """
        self.submission = get_object_or_404(
            ApplicationSubmission, id=self.kwargs["submission_pk"]
        )
        revisions = self.model.objects.filter(submission=self.submission).exclude(
            draft__isnull=False, live__isnull=True
        )

        filtered_revisions = revisions.filter(is_draft=False)

        # An edge case for when an instance has `SUBMISSIONS_DRAFT_ACCESS_STAFF=True`
        # and a staff member tries to view the revisions of the draft.
        if len(filtered_revisions) < 1:
            self.queryset = self.model.objects.filter(id=revisions.last().id)
        else:
            self.queryset = filtered_revisions

        return super().get_queryset()

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            submission=self.submission,
            **kwargs,
        )


@method_decorator(staff_required, name="dispatch")
class RevisionCompareView(DetailView):
    model = ApplicationSubmission
    template_name = "funds/revisions_compare.html"
    pk_url_kwarg = "submission_pk"

    def compare_revisions(self, from_data, to_data):
        self.object.form_data = from_data.form_data
        from_rendered_text_fields = self.object.render_text_blocks_answers()
        from_required = self.render_required()

        self.object.form_data = to_data.form_data
        to_rendered_text_fields = self.object.render_text_blocks_answers()
        to_required = self.render_required()

        required_fields = [
            compare(*fields) for fields in zip(from_required, to_required, strict=False)
        ]

        stream_fields = [
            compare(*fields)
            for fields in zip(
                from_rendered_text_fields, to_rendered_text_fields, strict=False
            )
        ]

        return (required_fields, stream_fields)

    def render_required(self):
        return [
            getattr(self.object, "get_{}_display".format(field))()
            for field in self.object.named_blocks
        ]

    def get_context_data(self, **kwargs):
        from_revision = self.object.revisions.get(id=self.kwargs["from"])
        to_revision = self.object.revisions.get(id=self.kwargs["to"])
        required_fields, stream_fields = self.compare_revisions(
            from_revision, to_revision
        )
        timestamps = (from_revision.timestamp, to_revision.timestamp)
        return super().get_context_data(
            timestamps=timestamps,
            required_fields=required_fields,
            stream_fields=stream_fields,
            **kwargs,
        )
