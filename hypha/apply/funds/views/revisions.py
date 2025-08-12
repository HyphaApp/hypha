import re
from typing import List

import nh3
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


def get_revisions(submission):
    """Get a queryset of all valid `ApplicationRevision`s that can be
    compared for the current submission

    This excludes draft & preview revisions unless draft(s) are the only
    existing revisions, in which the last draft will be returned in a QuerySet

    Returns:
        An [`ApplicationRevision`][hypha.apply.funds.models.ApplicationRevision] QuerySet
    """
    revisions = ApplicationRevision.objects.filter(submission=submission).exclude(
        draft__isnull=False, live__isnull=True
    )

    filtered_revisions = revisions.filter(is_draft=False)

    # An edge case for when an instance has `SUBMISSIONS_DRAFT_ACCESS_STAFF=True`
    # and a staff member tries to view the revisions of the draft.
    if len(filtered_revisions) < 1:
        return ApplicationRevision.objects.filter(id=revisions.last().id)
    else:
        return filtered_revisions


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
        self.queryset = get_revisions(submission=self.submission)

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

    # Specified to ensure template block order always aligns
    named_block_order = [
        "title",
        "full_name",
        "email",
        "address",
        "duration",
        "value",
        "organization",
    ]

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
            compare(*self.cleanse_stream_fields(*fields), should_clean=False)
            for fields in zip(
                from_rendered_text_fields, to_rendered_text_fields, strict=False
            )
        ]

        return (required_fields, stream_fields)

    def render_required(self):
        # Ensure named blocks are ordered according to the template
        ordered_name_blocks = [
            block
            for block in self.named_block_order
            if block in self.object.named_blocks
        ]
        return [
            getattr(self.object, "get_{}_display".format(field))()
            for field in ordered_name_blocks
        ]

    def get_context_data(self, **kwargs):
        from_revision = self.object.revisions.get(id=self.kwargs["from"])
        to_revision = self.object.revisions.get(id=self.kwargs["to"])
        required_fields, stream_fields = self.compare_revisions(
            from_revision, to_revision
        )
        ctx = {
            "all_revisions": get_revisions(submission=self.object),
            "from_revision": from_revision,
            "to_revision": to_revision,
            "required_fields": required_fields,
            "stream_fields": stream_fields,
        }
        return super().get_context_data(**ctx, **kwargs)

    def cleanse_stream_fields(self, a_field, b_field) -> List[str]:
        """Sanitizes the HTML outside of the h2 heading
        This is a temp fix and we should move to full HTML diffing

        Args:
            a_field: the field to sanitize
            b_field: the field to sanitize

        Returns:
            The sanitized stream field answers in a list
        """

        sanitized_answers = []

        for field in (a_field, b_field):
            # TODO: Using regex with HTML is not ideal but this temp until we move to xml parsing
            field_match = re.match(
                r"^\s*<section class=\".*\">\s*(<h2 class=\".*\">[\s\S]*?</h2>)([\s\S]*?)</section>",
                field,
            )
            try:
                # Keep h2 tags but purge any classes/attributes
                heading = nh3.clean(field_match.group(1), tags={"h2"}, attributes={})

                # Handle lists on the answer fields by subbing HTML for chars
                answer = re.sub("(<li[^>]*>)", r"\1◦ ", field_match.group(2))
                # Cleanse answer of HTML
                answer = nh3.clean(answer, attributes={}, tags=set())

                sanitized_answers.append(f"{heading}{answer}")
            except AttributeError:
                # If it fails to match for some reason just cleanse the fields but leave h2s
                answer = nh3.clean(answer, attributes={}, tags={"h2"})
                sanitized_answers.append(field)

        return sanitized_answers
