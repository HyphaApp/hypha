import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views import View

from hypha.apply.activity.messaging import MESSAGES, messenger

from ..forms import InviteCoApplicantForm
from ..models import ApplicationSubmission, CoApplicantInvite
from ..permissions import has_permission


@method_decorator(login_required, name="dispatch")
class CoApplicantInviteView(View):
    def dispatch(self, request, *args, **kwargs):
        self.submission = get_object_or_404(ApplicationSubmission, id=kwargs.get("pk"))
        permission, reason = has_permission(
            "co_applicant_invite",
            request.user,
            object=self.submission,
            raise_exception=False,
        )
        if not permission:
            messages.warning(self.request, reason)
            return HttpResponseRedirect(self.submission.get_absolute_url())
        return super(CoApplicantInviteView, self).dispatch(request, *args, **kwargs)

    def get(self, *args, **kwargs):
        reminder_form = InviteCoApplicantForm(
            submission=self.submission, user=self.request.user
        )
        return render(
            self.request,
            "funds/modals/invite_co_applicant_form.html",
            context={
                "form": reminder_form,
                "value": _("Invite"),
                "object": self.submission,
            },
        )

    def post(self, *args, **kwargs):
        form = InviteCoApplicantForm(
            self.request.POST,
            submission=self.submission,
            user=self.request.user,
        )
        if form.is_valid():
            co_applicant_invite = form.save()

            messenger(
                MESSAGES.INVITE_COAPPLICANT,
                request=self.request,
                user=self.request.user,
                source=co_applicant_invite.submission,
                related=co_applicant_invite,
            )
            return HttpResponse(
                status=204,
                headers={
                    "HX-Trigger": json.dumps(
                        {
                            "coApplicantUpdated": None,
                            "showMessage": _("Co-applicant created"),
                        }
                    ),
                },
            )
        return render(
            self.request,
            "funds/modals/invite_co_applicant_form.html",
            context={"form": form, "value": _("Invite"), "object": self.submission},
            status=400,
        )


class CoApplicantInviteAcceptView(View):
    pass


@login_required
def list_invites(request):
    return CoApplicantInvite.objects.all()
