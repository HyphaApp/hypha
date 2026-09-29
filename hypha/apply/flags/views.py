from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from django.views import View

from hypha.apply.funds.models import ApplicationSubmission

from .models import Flag


@method_decorator(login_required, name="dispatch")
class FlagSubmissionCreateView(UserPassesTestMixin, View):
    model = Flag

    def post(self, request, type, submission_pk):
        if type not in self.model.FLAG_TYPES:
            return HttpResponseBadRequest()

        # Only staff can create staff flags.
        if type == self.model.STAFF and not request.user.is_apply_staff:
            return HttpResponseForbidden()

        submission = get_object_or_404(ApplicationSubmission, pk=submission_pk)
        if submission.is_archive:
            return HttpResponseForbidden()

        submission_type = ContentType.objects.get_for_model(ApplicationSubmission)
        flags = self.model.objects.filter(
            target_object_id=submission.pk,
            target_content_type=submission_type,
            type=type,
        )
        if type == self.model.USER:
            # User flags are personal bookmarks, scoped to the acting user.
            flags = flags.filter(user=request.user)

        # Staff flags are shared, any staff member can clear one, whoever set it.
        if flags.exists():
            flags.delete()
        else:
            self.model.objects.create(
                user=request.user,
                target_object_id=submission.pk,
                target_content_type=submission_type,
                type=type,
            )

        return render(
            request,
            "flags/flags.html",
            {"submission": submission, "user": request.user},
        )

    def test_func(self):
        return self.request.user.is_apply_staff or self.request.user.is_reviewer
