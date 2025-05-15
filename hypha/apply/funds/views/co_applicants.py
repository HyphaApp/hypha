import datetime
import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.db.models import Case, IntegerField, Value, When
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import gettext as _
from django.views import View
from django_htmx.http import HttpResponseClientRedirect
from two_factor.utils import default_device

from hypha.apply.activity.messaging import MESSAGES, messenger
from hypha.apply.users.models import User
from hypha.apply.users.roles import APPLICANT_GROUP_NAME
from hypha.apply.users.services import PasswordlessAuthService
from hypha.apply.users.tokens import CoApplicantInviteTokenGenerator

from ..forms import EditCoApplicantForm, InviteCoApplicantForm
from ..models import ApplicationSubmission, CoApplicant, CoApplicantInvite
from ..models.co_applicants import CoApplicantInviteStatus
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
        invite_form = InviteCoApplicantForm(
            submission=self.submission, user=self.request.user
        )
        return render(
            self.request,
            "funds/modals/invite_co_applicant_form.html",
            context={
                "form": invite_form,
                "value": _("Invite"),
                "object": self.submission,
                "expiry": settings.PASSWORD_RESET_TIMEOUT // (60 * 60 * 24),
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
            form.instance.role = form.cleaned_data["role"]
            form.instance.invited_by = self.request.user
            form.instance.invited_at = timezone.now()
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
        try:
            self.invite = CoApplicantInvite.objects.get(
                pk=force_str(urlsafe_base64_decode(kwargs.get("uidb64")))
            )
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return render(
                self.request,
                "funds/coapplicant_invite_landing_page.html",
                context={"is_valid": False},
                status=200,
            )
        if (
            self.invite
            and self.check_token(self.invite, token)
            and self.invite.status == CoApplicantInviteStatus.PENDING
        ):
            return super().dispatch(request, *args, **kwargs)
        return render(
            self.request,
            "funds/coapplicant_invite_landing_page.html",
            context={"is_valid": False},
            status=200,
        )

    def check_token(self, invite, token):
        token_generator = CoApplicantInviteTokenGenerator()
        return token_generator.check_token(invite, token)

    def get(self, *args, **kwargs):
        user = User.objects.filter(email=self.invite.invited_user_email).first()
        if user and (user.is_apply_staff or user.is_apply_staff_admin):
            return HttpResponseRedirect(reverse_lazy("dashboard:dashboard"))
        return render(
            self.request,
            "funds/coapplicant_invite_landing_page.html",
            context={
                "invite": self.invite,
                "is_valid": True,
                "two_factor_required": settings.ENFORCE_TWO_FACTOR,
            },
            status=200,
        )

    def post(self, args, **kwargs):
        action = self.request.POST.get("action")
        if action == "accept":
            self.invite.status = CoApplicantInviteStatus.ACCEPTED
            self.invite.responded_on = datetime.datetime.now()
            self.invite.save(update_fields=["status", "responded_on"])

            # handle auto login/signup
            user, created = User.objects.get_or_create(
                email=self.invite.invited_user_email, is_active=True
            )
            if created:
                applicant_group = Group.objects.get(name=APPLICANT_GROUP_NAME)
                user.groups.add(applicant_group)
                user.set_unusable_password()
                user.save()

            # create Co-applicant and add to submission
            co_applicant, created = CoApplicant.objects.get_or_create(
                invite=self.invite,
                submission=self.invite.submission,
                user=user,
                role=self.invite.role,
            )

            if not self.request.user.is_authenticated or self.request.user != user:
                user.backend = settings.CUSTOM_AUTH_BACKEND
                if settings.ENFORCE_TWO_FACTOR:
                    if default_device(user):
                        service = PasswordlessAuthService(
                            self.request,
                            redirect_field_name=self.get_success_url(),
                        )
                        login_path = service._get_login_path(user)
                        return HttpResponseClientRedirect(login_path)
                    login(self.request, user)
                    return HttpResponseClientRedirect(
                        reverse_lazy("two_factor:setup")
                        + f"?next={self.get_success_url()}"
                    )

                login(self.request, user)
            return HttpResponseClientRedirect(self.get_success_url())
        self.invite.status = CoApplicantInviteStatus.REJECTED
        self.invite.responded_on = datetime.datetime.now()
        self.invite.save(update_fields=["status", "responded_on"])
        if self.request.user.is_authenticated:
            return HttpResponseClientRedirect(reverse_lazy("dashboard:dashboard"))
        return HttpResponseClientRedirect("/")

    def get_success_url(self):
        return reverse_lazy(
            "apply:submissions:detail", args=(self.invite.submission.pk,)
        )


class EditCoApplicantView(View):
    def dispatch(self, request, *args, **kwargs):
        self.invite = get_object_or_404(CoApplicantInvite, id=kwargs.get("invite_pk"))
        has_permission(
            "co_applicants_update",
            user=request.user,
            object=self.invite,
            raise_exception=True,
        )
        return super(EditCoApplicantView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        if self.invite.status == CoApplicantInviteStatus.ACCEPTED:
            form = EditCoApplicantForm(instance=self.invite.co_applicant)
            co_applicant_exists = True
        else:
            form = EditCoApplicantForm(instance=self.invite)
            co_applicant_exists = False
        return render(
            request,
            "funds/modals/edit_co_applicant_form.html",
            context={
                "form": form,
                "invite": self.invite,
                "value": _("Save"),
                "co_applicant_exists": co_applicant_exists,
            },
            status=200,
        )

    def post(self, request, *args, **kwargs):
        if self.invite.status == CoApplicantInviteStatus.ACCEPTED:
            form = EditCoApplicantForm(
                self.request.POST, instance=self.invite.co_applicant
            )
            if form.is_valid():
                form.save()

        return HttpResponse(
            status=204,
            headers={
                "HX-Trigger": json.dumps(
                    {
                        "coApplicantUpdated": None,
                        "showMessage": _("Co-applicant updated"),
                    }
                ),
            },
        )


def co_applicant_re_invite_view(request, invite_pk):
    invite = get_object_or_404(CoApplicantInvite, id=invite_pk)
    has_permission(
        "co_applicants_update", user=request.user, object=invite, raise_exception=True
    )
    invite.status = CoApplicantInviteStatus.PENDING
    invite.invited_at = timezone.now()
    invite.save(update_fields=["status", "invited_at"])
    messenger(
        MESSAGES.INVITE_COAPPLICANT,
        request=request,
        user=request.user,
        source=invite.submission,
        related=invite,
    )
    return HttpResponse(
        status=204,
        headers={
            "HX-Trigger": json.dumps(
                {
                    "coApplicantUpdated": None,
                    "showMessage": _("Co-applicant re-invited"),
                }
            ),
        },
    )


def co_applicant_invite_delete_view(request, invite_pk):
    invite = get_object_or_404(CoApplicantInvite, id=invite_pk)
    has_permission(
        "co_applicants_update", user=request.user, object=invite, raise_exception=True
    )
    if hasattr(invite, "co_applicant"):
        invite.co_applicant.delete()
    invite.delete()

    return HttpResponse(
        status=204,
        headers={
            "HX-Trigger": json.dumps(
                {
                    "coApplicantUpdated": None,
                    "showMessage": _("Co-applicant deleted"),
                }
            ),
        },
    )


@login_required
def list_coapplicant_invites(request, pk):
    submission = get_object_or_404(ApplicationSubmission, pk=pk)
    has_permission(
        "co_applicants_view", user=request.user, object=submission, raise_exception=True
    )
    status_order = Case(
        When(status="accepted", then=Value(0)),
        When(status="pending", then=Value(1)),
        When(status="rejected", then=Value(2)),
        When(status="expired", then=Value(3)),
        default=Value(4),
        output_field=IntegerField(),
    )
    co_applicant_invites = (
        CoApplicantInvite.objects.filter(submission=submission)
        .annotate(status_priority=status_order)
        .order_by("status_priority", "-responded_on", "-created_at")
    )

    # check if pending invites have expired, update status
    for invite in co_applicant_invites.filter(status=CoApplicantInviteStatus.PENDING):
        if (
            int((timezone.now() - invite.invited_at).total_seconds())
            > CoApplicantInviteTokenGenerator().TIMEOUT
        ):
            invite.status = CoApplicantInviteStatus.EXPIRED
            invite.save(update_fields=["status"])

    return render(
        request,
        "funds/includes/co-applicant-block.html",
        context={
            "co_applicants": co_applicant_invites,
            "object": submission,
            "invite_max_limit": settings.SUBMISSIONS_COAPPLICANT_INVITES_LIMIT,
        },
        status=200,
    )
