from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseNotAllowed, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View

from hypha.apply.funds.models import ApplicationSubmission

from .models import Bookmark


@method_decorator(login_required, name="dispatch")
class BookmarkSubmissionCreateView(UserPassesTestMixin, View):
    model = Bookmark

    def post(self, request, type, submission_pk):
        if request.headers.get("x-requested-with") != "XMLHttpRequest":
            return HttpResponseNotAllowed()

        # Only staff can create staff bookmarks.
        if type == self.model.STAFF and not self.request.user.is_apply_staff:
            return HttpResponseNotAllowed()

        submission_type = ContentType.objects.get_for_model(ApplicationSubmission)
        # Trying to get a bookmark from the table, or create a new one
        bookmark, created = self.model.objects.get_or_create(
            user=request.user,
            target_object_id=submission_pk,
            target_content_type=submission_type,
            type=type,
        )
        # If no new bookmark has been created,
        # Then we believe that the request was to delete the bookmark.
        if not created:
            bookmark.delete()

        return JsonResponse({"result": created})

    def test_func(self):
        return self.request.user.is_apply_staff or self.request.user.is_reviewer
