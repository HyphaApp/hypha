from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseNotAllowed, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View

from hypha.apply.funds.models import ApplicationSubmission

from .models import Flag


@method_decorator(login_required, name='dispatch')
class FlagSubmissionCreateView(UserPassesTestMixin, View):
    model = Flag

    def post(self, request, type, submission_pk):
        if not request.is_ajax():
            return HttpResponseNotAllowed()

        # Only staff can create staff flags.
        if type == self.model.STAFF and not self.request.user.is_apply_staff:
            return HttpResponseNotAllowed()

        submission_type = ContentType.objects.get_for_model(ApplicationSubmission)
        # Trying to get a flag from the table, or create a new one
        flag, created = self.model.objects.get_or_create(user=request.user, target_object_id=submission_pk, target_content_type=submission_type, type=type)
        # If no new flag has been created,
        # Then we believe that the request was to delete the flag.
        if not created:
            flag.delete()

        return JsonResponse({"result": created})

    def test_func(self):
        return self.request.user.is_apply_staff or self.request.user.is_reviewer
