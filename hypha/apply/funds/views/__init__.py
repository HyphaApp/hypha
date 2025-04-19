from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin

from hypha.apply.users.decorators import staff_required
from hypha.apply.utils.storage import PrivateMediaView

from ..files import generate_private_file_path
from ..models import (
    ApplicationSubmission,
    RoundsAndLabs,
)
from ..permissions import has_permission
from ..tables import (
    RoundsFilter,
    RoundsTable,
)


def submission_success(request, pk):
    submission = get_object_or_404(ApplicationSubmission, pk=pk)
    return render(
        request,
        "funds/submission-success.html",
        {
            "form_submission": submission,
        },
    )


@method_decorator(staff_required, name="dispatch")
class RoundListView(SingleTableMixin, FilterView):
    template_name = "funds/rounds.html"
    table_class = RoundsTable
    filterset_class = RoundsFilter

    def get_queryset(self):
        return RoundsAndLabs.objects.with_progress()


@method_decorator(login_required, name="dispatch")
class SubmissionPrivateMediaView(UserPassesTestMixin, PrivateMediaView):
    raise_exception = True

    def dispatch(self, *args, **kwargs):
        submission_pk = self.kwargs["pk"]
        self.submission = get_object_or_404(ApplicationSubmission, pk=submission_pk)
        return super().dispatch(*args, **kwargs)

    def get_media(self, *args, **kwargs):
        field_id = kwargs["field_id"]
        file_name = kwargs["file_name"]
        path_to_file = generate_private_file_path(
            self.submission.pk, field_id, file_name
        )
        return self.storage.open(path_to_file)

    def test_func(self):
        permission, _ = has_permission(
            "submission_view", self.request.user, self.submission
        )
        return permission
