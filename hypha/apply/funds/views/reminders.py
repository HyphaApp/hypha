import json

from django.contrib import messages
from django.contrib.auth.decorators import (
    login_required,
    user_passes_test,
)
from django.http import (
    HttpResponse,
    HttpResponseRedirect,
)
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views import View
from django.views.decorators.http import require_http_methods
from django.views.generic import DeleteView

from hypha.apply.activity.messaging import MESSAGES, messenger
from hypha.apply.users.decorators import (
    is_apply_staff,
    staff_required,
)

from ..forms import CreateReminderForm
from ..models import (
    ApplicationSubmission,
    Reminder,
)
from ..permissions import has_permission


@login_required
@user_passes_test(is_apply_staff)
@require_http_methods(["GET"])
def reminder_list(request, pk):
    submission = get_object_or_404(ApplicationSubmission, id=pk)
    reminders = Reminder.objects.filter(submission=submission)
    return render(
        request,
        "funds/includes/reminders_block.html",
        context={"reminders": reminders, "object": submission},
    )


@method_decorator(staff_required, name="dispatch")
class ReminderCreateView(View):
    def dispatch(self, request, *args, **kwargs):
        self.submission = get_object_or_404(ApplicationSubmission, id=kwargs.get("pk"))
        permission, reason = has_permission(
            "submission_edit",
            request.user,
            object=self.submission,
            raise_exception=False,
        )
        if not permission:
            messages.warning(self.request, reason)
            return HttpResponseRedirect(self.submission.get_absolute_url())
        return super(ReminderCreateView, self).dispatch(request, *args, **kwargs)

    def get(self, *args, **kwargs):
        reminder_form = CreateReminderForm(instance=self.submission)
        return render(
            self.request,
            "funds/includes/create_reminder_form.html",
            context={
                "form": reminder_form,
                "value": _("Create Reminder"),
                "object": self.submission,
            },
        )

    def post(self, *args, **kwargs):
        form = CreateReminderForm(
            self.request.POST, instance=self.submission, user=self.request.user
        )
        if form.is_valid():
            reminder = form.save()
            messenger(
                MESSAGES.CREATE_REMINDER,
                request=self.request,
                user=self.request.user,
                source=self.submission,
                related=reminder,
            )
            return HttpResponse(
                status=204,
                headers={
                    "HX-Trigger": json.dumps({"remindersUpdated": None}),
                },
            )
        return render(
            self.request,
            "funds/includes/create_reminder_form.html",
            context={"form": form, "value": _("Create"), "object": self.submission},
            status=400,
        )


@method_decorator(staff_required, name="dispatch")
class ReminderDeleteView(DeleteView):
    model = Reminder

    def get_success_url(self):
        submission = get_object_or_404(
            ApplicationSubmission, id=self.kwargs["submission_pk"]
        )
        return reverse_lazy("funds:submissions:detail", args=(submission.id,))

    def form_valid(self, form):
        reminder = self.get_object()
        messenger(
            MESSAGES.DELETE_REMINDER,
            user=self.request.user,
            request=self.request,
            source=reminder.submission,
            related=reminder,
        )
        return super().form_valid(form)
