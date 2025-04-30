import datetime
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views import View
from django_htmx.http import HttpResponseClientRedirect

from hypha.apply.activity.messaging import MESSAGES, messenger

from ..forms import InviteCoApplicantForm
from ..models import ApplicationSubmission, CoApplicantInvite
from ..models.co_applicants import CoApplicantInviteStatus
from ..permissions import has_permission
from ..utils import verify_signed_token


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
            form.instance.submission = self.submission
            form.instance.invited_user_email = form.cleaned_data["invited_user_email"]
            form.instance.invited_by = self.request.user
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
    def dispatch(self, request, *args, **kwargs):
        token = kwargs.get("token")
        data = verify_signed_token(
            token=token, salt="co-applicant-invite-token", max_age=7 * 86400
        )  # 7 days as expiry
        if data:
            email = data.get("email")
            submission_pk = data.get("submission")
            self.invite = get_object_or_404(
                CoApplicantInvite,
                invited_user_email=email,
                submission__id=submission_pk,
            )
            if self.invite.status != CoApplicantInviteStatus.PENDING:
                raise Http404("Invalid: Invite already used")
            return super().dispatch(request, *args, **kwargs)
        raise Http404("Invalid: Invite not found")

    def get(self, *args, **kwargs):
        return render(
            self.request,
            "funds/coapplicant_invite_landing_page.html",
            context={"submission": self.invite.submission},
            status=200,
        )

    def post(self, args, **kwargs):
        action = self.request.POST.get("action")
        if action == "accept":
            self.invite.status = CoApplicantInviteStatus.ACCEPTED
            self.invite.responded_on = datetime.datetime.now()
            self.invite.save(update_fields=["status", "responded_on"])

            # handle auto login/signup

            return HttpResponseClientRedirect(
                reverse_lazy(
                    "apply:submissions:detail", args=(self.invite.submission.pk,)
                )
            )
        self.invite.status = CoApplicantInviteStatus.REJECTED
        self.invite.responded_on = datetime.datetime.now()
        self.invite.save(update_fields=["status", "responded_on"])
        return HttpResponseClientRedirect("/")


@login_required
def list_invites(request):
    return CoApplicantInvite.objects.all()
