import datetime
import time
from typing import Any
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login, update_session_auth_hash
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.forms import AdminPasswordChangeForm
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth.views import INTERNAL_RESET_SESSION_TOKEN
from django.contrib.auth.views import (
    PasswordResetConfirmView as DjPasswordResetConfirmView,
)
from django.contrib.auth.views import PasswordResetView as DjPasswordResetView
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import PermissionDenied
from django.core.signing import TimestampSigner, dumps, loads
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import Http404, get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import UpdateView
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from django_htmx.http import HttpResponseClientRedirect
from django_otp import devices_for_user
from django_ratelimit.decorators import ratelimit
from elevate.mixins import ElevateMixin
from elevate.utils import grant_elevated_privileges
from elevate.views import redirect_to_elevate
from hijack.views import AcquireUserView
from two_factor.forms import AuthenticationTokenForm, BackupTokenForm
from two_factor.utils import default_device, get_otpauth_url, totp_digits
from two_factor.views import BackupTokensView as TwoFactorBackupTokensView
from two_factor.views import DisableView as TwoFactorDisableView
from two_factor.views import LoginView as TwoFactorLoginView
from two_factor.views import SetupView as TwoFactorSetupView
from wagtail.admin.views.account import password_management_enabled
from wagtail.models import Site
from wagtail.users.views.users import change_user_perm

from hypha.core.mail import MarkdownMail
from hypha.home.models import ApplyHomePage

from .decorators import require_oauth_whitelist
from .forms import (
    BecomeUserForm,
    CustomAuthenticationForm,
    Disable2FAConfirmationForm,
    PasswordlessAuthForm,
    ProfileForm,
)
from .models import ConfirmAccessToken, PendingSignup
from .services import PasswordlessAuthService
from .tokens import PasswordlessLoginTokenGenerator, PasswordlessSignupTokenGenerator
from .utils import (
    generate_numeric_token,
    get_redirect_url,
    send_activation_email,
    send_confirmation_email,
)

User = get_user_model()


@method_decorator(
    ratelimit(key="ip", rate=settings.DEFAULT_RATE_LIMIT, method="POST"),
    name="dispatch",
)
@method_decorator(
    ratelimit(key="post:email", rate=settings.DEFAULT_RATE_LIMIT, method="POST"),
    name="dispatch",
)
class LoginView(TwoFactorLoginView):
    form_list = (
        ("auth", CustomAuthenticationForm),
        ("token", AuthenticationTokenForm),
        ("backup", BackupTokenForm),
    )

    redirect_field_name = "next"
    redirect_authenticated_user = True
    template_name = "users/login.html"

    def get_context_data(self, form, **kwargs):
        context_data = super(LoginView, self).get_context_data(form, **kwargs)
        context_data["is_public_site"] = True
        context_data["redirect_url"] = get_redirect_url(
            self.request, self.redirect_field_name
        )
        if (
            Site.find_for_request(self.request)
            == ApplyHomePage.objects.first().get_site()
        ):
            context_data["is_public_site"] = False
        return context_data


@method_decorator(login_required, name="dispatch")
class AccountView(UpdateView):
    form_class = ProfileForm
    template_name = "users/account.html"

    def get_object(self):
        return self.request.user

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def form_valid(self, form):
        updated_email = form.cleaned_data["email"]
        name = form.cleaned_data["full_name"]
        slack = form.cleaned_data.get("slack", "")
        user = get_object_or_404(User, id=self.request.user.id)
        if user.email != updated_email:
            base_url = reverse("users:email_change_confirm_password")
            query_dict = {"updated_email": updated_email, "name": name, "slack": slack}

            signer = TimestampSigner()
            signed_value = signer.sign(dumps(query_dict))
            return redirect(
                "{}?{}".format(base_url, urlencode({"value": signed_value}))
            )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("users:account")

    def get_context_data(self, **kwargs):
        if self.request.user.is_superuser and settings.HIJACK_ENABLE:
            swappable_form = BecomeUserForm()
        else:
            swappable_form = None

        show_change_password = (
            password_management_enabled() and self.request.user.has_usable_password(),
        )

        return super().get_context_data(
            swappable_form=swappable_form,
            default_device=default_device(self.request.user),
            show_change_password=show_change_password,
            **kwargs,
        )


@login_required
def account_email_change(request):
    if request.user.has_usable_password() and not request.is_elevated():
        return redirect_to_elevate(request.get_full_path())

    signer = TimestampSigner()
    try:
        unsigned_value = signer.unsign(
            request.GET.get("value"), max_age=settings.PASSWORD_PAGE_TIMEOUT
        )
    except Exception:
        messages.error(
            request,
            _("Password Page timed out. Try changing the email again."),
        )
        return redirect("users:account")
    value = loads(unsigned_value)

    if slack := value["slack"] is not None:
        request.user.slack = slack

    request.user.full_name = value["name"]
    request.user.save()

    if request.user.email != value["updated_email"]:
        send_confirmation_email(
            request.user,
            signer.sign(dumps(value["updated_email"])),
            updated_email=value["updated_email"],
            site=Site.find_for_request(request),
        )

    # alert email
    request.user.email_user(
        subject="Alert! An attempt to update your email.",
        message=render_to_string(
            "users/email_change/update_info_email.html",
            {
                "name": request.user.get_full_name(),
                "username": request.user.get_username(),
                "org_email": settings.ORG_EMAIL,
                "org_short_name": settings.ORG_SHORT_NAME,
                "org_long_name": settings.ORG_LONG_NAME,
            },
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
    )
    return redirect("users:confirm_link_sent")


@method_decorator(login_required, name="dispatch")
class EmailChangeDoneView(TemplateView):
    template_name = "users/email_change/done.html"
    title = _("Verify Email")


@login_required()
def become(request):
    if not settings.HIJACK_ENABLE:
        raise Http404(_("Hijack feature is not enabled."))

    if not request.user.is_superuser:
        raise PermissionDenied()

    id = request.POST.get("user_pk")
    if request.POST and id:
        target_user = User.objects.get(pk=id)
        if target_user.is_superuser:
            raise PermissionDenied()

        return AcquireUserView.as_view()(request)
    return redirect("users:account")


@login_required()
@require_oauth_whitelist
def oauth(request):
    """Generic, empty view for the OAuth associations."""

    return TemplateResponse(request, "users/oauth.html", {})


@method_decorator(login_required, name="dispatch")
class EmailChangeConfirmationView(TemplateView):
    def get(self, request, *args, **kwargs):
        user = self.get_user(kwargs.get("uidb64"))
        email = self.unsigned(kwargs.get("token"))
        if user and email:
            if user.email != email:
                user.email = email
                user.save()
                messages.success(
                    request, _(f"Your email has been successfully updated to {email}!")
                )
            return redirect("users:account")

        return render(request, "users/email_change/invalid_link.html")

    def unsigned(self, token):
        signer = TimestampSigner()
        try:
            unsigned_value = signer.unsign(
                token,
                max_age=datetime.timedelta(seconds=settings.PASSWORD_RESET_TIMEOUT),
            )
        except Exception:
            return False
        return loads(unsigned_value)

    def get_user(self, uidb64):
        """
        Given the verified uid, look up and return the
        corresponding user account if it exists, or ``None`` if it
        doesn't.
        """
        try:
            user = User.objects.get(**{"pk": force_str(urlsafe_base64_decode(uidb64))})
            return user
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return None


class ActivationView(TemplateView):
    redirect_field_name = "next"

    def get(self, request, *args, **kwargs):
        user = self.get_user(kwargs.get("uidb64"))

        if self.valid(user, kwargs.get("token")):
            user.backend = settings.CUSTOM_AUTH_BACKEND
            login(request, user)
            if settings.WAGTAILUSERS_PASSWORD_ENABLED and settings.ENABLE_PUBLIC_SIGNUP:
                # In this case, the user entered a password while registering,
                # and so they shouldn't need to activate a password
                return redirect("users:account")
            else:
                url = reverse("users:activate_password")
                if redirect_url := get_redirect_url(request, self.redirect_field_name):
                    url = f"{url}?next={redirect_url}"
                return redirect(url)

        return render(request, "users/activation/invalid.html")

    def valid(self, user, token):
        """
        Verify that the activation token is valid and within the
        permitted activation time window.
        """

        token_generator = PasswordResetTokenGenerator()
        return user is not None and token_generator.check_token(user, token)

    def get_user(self, uidb64):
        """
        Given the verified uid, look up and return the
        corresponding user account if it exists, or ``None`` if it
        doesn't.
        """
        try:
            user = User.objects.get(**{"pk": force_str(urlsafe_base64_decode(uidb64))})
            return user
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return None


def create_password(request):
    """
    A custom view for the admin password change form used for account activation.
    """
    redirect_url = get_redirect_url(request, redirect_field="next")

    if request.method == "POST":
        form = AdminPasswordChangeForm(request.user, request.POST)

        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, "Your password was successfully updated!")
            if redirect_url:
                return redirect(redirect_url)
            return redirect("users:account")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = AdminPasswordChangeForm(request.user)

    return render(
        request,
        "users/change_password.html",
        {
            "form": form,
            "redirect_url": redirect_url,
        },
    )


@method_decorator(
    ratelimit(key="post:email", rate=settings.DEFAULT_RATE_LIMIT, method="POST"),
    name="dispatch",
)
@method_decorator(
    ratelimit(key="ip", rate=settings.DEFAULT_RATE_LIMIT, method="POST"),
    name="dispatch",
)
class PasswordResetView(DjPasswordResetView):
    redirect_field_name = "next"
    email_template_name = "users/password_reset/email.txt"
    template_name = "users/password_reset/form.html"
    success_url = reverse_lazy("users:password_reset_done")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["redirect_url"] = get_redirect_url(self.request, self.redirect_field_name)
        return ctx

    def get_extra_email_context(self):
        return {
            "redirect_url": get_redirect_url(self.request, self.redirect_field_name),
            "site": Site.find_for_request(self.request),
            "org_short_name": settings.ORG_SHORT_NAME,
            "org_long_name": settings.ORG_LONG_NAME,
        }

    def form_valid(self, form):
        """
        Overrides default django form_valid to pass extra context to send_email method
        """
        opts = {
            "use_https": self.request.is_secure(),
            "token_generator": self.token_generator,
            "from_email": self.from_email,
            "email_template_name": self.email_template_name,
            "subject_template_name": self.subject_template_name,
            "request": self.request,
            "html_email_template_name": self.html_email_template_name,
            "extra_email_context": self.get_extra_email_context(),
        }
        form.save(**opts)
        return HttpResponseRedirect(self.get_success_url())


@method_decorator(never_cache, name="dispatch")
@method_decorator(login_required, name="dispatch")
class TWOFASetupView(TwoFactorSetupView):
    def get_issuer(self):
        return get_current_site(self.request).name

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form, **kwargs)
        if self.steps.current == "generator":
            try:
                username = self.request.user.get_username()
            except AttributeError:
                username = self.request.user.username

            otpauth_url = get_otpauth_url(
                accountname=username,
                issuer=self.get_issuer(),
                secret=context["secret_key"],
                digits=totp_digits(),
            )
            context.update(
                {
                    "otpauth_url": otpauth_url,
                }
            )

        return context


@method_decorator(
    ratelimit(key="user", rate=settings.DEFAULT_RATE_LIMIT, method="POST"),
    name="dispatch",
)
@method_decorator(login_required, name="dispatch")
class TWOFADisableView(ElevateMixin, TwoFactorDisableView):
    """
    View for disabling two-factor for a user's account.
    """

    template_name = "two_factor/profile/disable.html"
    success_url = reverse_lazy("users:account")
    form_class = Disable2FAConfirmationForm


@method_decorator(
    permission_required(change_user_perm, raise_exception=True), name="dispatch"
)
class TWOFAAdminDisableView(ElevateMixin, FormView):
    """
    View for PasswordForm to confirm the Disable 2FA process on wagtail admin.
    """

    form_class = Disable2FAConfirmationForm
    template_name = "two_factor/admin/disable.html"
    user = None

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # store the user from url for redirecting to the same user's account edit page
        self.user = get_object_or_404(User, pk=self.kwargs.get("user_id"))
        return kwargs

    def form_valid(self, form):
        for device in devices_for_user(self.user):
            device.delete()
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("wagtailusers_users:edit", args=[self.user.id])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["user"] = self.user
        return ctx


def mfa_failure_view(
    request, reason, template_name="two_factor/core/two_factor_required.html"
):
    """Renders a template asking the user to setup 2FA.

    Used by hypha.apply.users.middlewares.TwoFactorAuthenticationMiddleware,
    if ENFORCE_TWO_FACTOR is enabled.
    """
    ctx = {
        "reason": reason,
    }
    return render(request, template_name, ctx)


class BackupTokensView(ElevateMixin, TwoFactorBackupTokensView):
    pass


class PasswordResetConfirmView(DjPasswordResetConfirmView):
    redirect_field_name = "next"
    template_name = "users/password_reset/confirm.html"
    post_reset_login = True
    post_reset_login_backend = settings.CUSTOM_AUTH_BACKEND
    success_url = reverse_lazy("users:account")

    def get_success_url(self) -> str:
        if next_path := get_redirect_url(self.request, self.redirect_field_name):
            return next_path
        return super().get_success_url()

    def get_context_data(self, **kwargs: Any) -> Any:
        context = super().get_context_data(**kwargs)
        context["redirect_url"] = get_redirect_url(
            self.request, self.redirect_field_name
        )
        return context

    @method_decorator(sensitive_post_parameters())
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        assert "uidb64" in kwargs and "token" in kwargs

        self.validlink = False
        self.user = self.get_user(kwargs["uidb64"])

        if self.user is not None:
            token = kwargs["token"]
            if token == self.reset_url_token:
                session_token = self.request.session.get(INTERNAL_RESET_SESSION_TOKEN)
                if self.token_generator.check_token(self.user, session_token):
                    # If the token is valid, display the password reset form.
                    self.validlink = True
                    return super().dispatch(*args, **kwargs)
            else:
                if self.token_generator.check_token(self.user, token):
                    # Store the token in the session and redirect to the
                    # password reset form at a URL without the token. That
                    # avoids the possibility of leaking the token in the
                    # HTTP Referer header.
                    self.request.session[INTERNAL_RESET_SESSION_TOKEN] = token
                    redirect_url = self.request.path.replace(
                        token, self.reset_url_token
                    )

                    # Add handler for '?next' redirect parameter.
                    if next_path := get_redirect_url(
                        self.request, self.redirect_field_name
                    ):
                        redirect_url = f"{redirect_url}?next={next_path}"

                    return HttpResponseRedirect(redirect_url)


@method_decorator(
    ratelimit(key="ip", rate=settings.DEFAULT_RATE_LIMIT, method="POST"),
    name="dispatch",
)
@method_decorator(
    ratelimit(key="post:email", rate=settings.DEFAULT_RATE_LIMIT, method="POST"),
    name="dispatch",
)
class PasswordLessLoginSignupView(FormView):
    """This view is used to collect the email address for passwordless login/signup.

    If the email address is already associated with an account, an email is sent. If not,
    if the registration is enabled an email is sent, to allow the user to create an account.

    NOTE: This view should never expose whether an email address is associated with an account.
    """

    template_name = "users/passwordless_login_signup.html"
    redirect_field_name = "next"
    http_method_names = ["get", "post"]
    form_class = PasswordlessAuthForm

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(settings.LOGIN_REDIRECT_URL)

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        if self.request.htmx:
            ctx["base_template"] = "includes/_partial-main.html"
        else:
            ctx["base_template"] = "base-apply.html"
        ctx["redirect_url"] = get_redirect_url(self.request, self.redirect_field_name)
        return ctx

    def post(self, request):
        form = self.get_form()
        if form.is_valid():
            service = PasswordlessAuthService(
                request, redirect_field_name=self.redirect_field_name
            )

            email = form.cleaned_data["email"]
            service.initiate_login_signup(email=email)

            return TemplateResponse(
                self.request,
                "users/partials/passwordless_login_signup_sent.html",
                self.get_context_data(),
            )
        else:
            return self.render_to_response(self.get_context_data(form=form))


class PasswordlessLoginView(LoginView):
    """This view is used to capture the passwordless login token and log the user in.

    If the token is valid, the user is logged in and redirected to the dashboard.
    If the token is invalid, the user is shown invalid token page.

    This view inherits from LoginView to reuse the 2FA views, if a mfa device is added
    to the user.
    """

    def get(self, request, uidb64, token, *args, **kwargs):
        try:
            user = User.objects.get(pk=force_str(urlsafe_base64_decode(uidb64)))
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user and self.check_token(user, token):
            user.backend = settings.CUSTOM_AUTH_BACKEND

            if default_device(user):
                # User has mfa, set the user details and redirect to 2fa login
                self.storage.reset()
                self.storage.authenticated_user = user
                self.storage.data["authentication_time"] = int(time.time())
                return self.render_goto_step("token")

            # No mfa, log the user in
            login(request, user)

            if redirect_url := get_redirect_url(request, self.redirect_field_name):
                return redirect(redirect_url)

            return redirect("dashboard:dashboard")

        return render(request, "users/activation/invalid.html")

    def check_token(self, user, token):
        token_generator = PasswordlessLoginTokenGenerator()
        return token_generator.check_token(user, token)


class PasswordlessSignupView(TemplateView):
    """This view is used to capture the passwordless login token and log the user in.

    If the token is valid, the user is logged in and redirected to the dashboard.
    If the token is invalid, the user is shown invalid token page.
    """

    redirect_field_name = "next"

    def get(self, request, *args, **kwargs):
        pending_signup = self.get_pending_signup(kwargs.get("uidb64"))
        token = kwargs.get("token")
        token_generator = PasswordlessSignupTokenGenerator()

        if pending_signup and token_generator.check_token(pending_signup, token):
            user = User.objects.create(email=pending_signup.email, is_active=True)
            user.set_unusable_password()
            user.save()
            pending_signup.delete()

            user.backend = settings.CUSTOM_AUTH_BACKEND
            login(request, user)

            redirect_url = get_redirect_url(request, self.redirect_field_name)

            if redirect_url:
                return redirect(redirect_url)

            # If 2FA is enabled, redirect to setup page instead of dashboard
            if settings.ENFORCE_TWO_FACTOR:
                redirect_url = redirect_url or reverse("dashboard:dashboard")
                return redirect(reverse("two_factor:setup") + f"?next={redirect_url}")

            return redirect("dashboard:dashboard")

        return render(request, "users/activation/invalid.html")

    def get_pending_signup(self, uidb64):
        """
        Given the verified uid, look up and return the corresponding user
        account if it exists, or `None` if it doesn't.
        """
        try:
            return PendingSignup.objects.get(
                **{"pk": force_str(urlsafe_base64_decode(uidb64))}
            )
        except (TypeError, ValueError, OverflowError, PendingSignup.DoesNotExist):
            return None


@login_required
def send_confirm_access_email_view(request):
    """Sends email with link to login in an elevated mode."""
    token_obj, _ = ConfirmAccessToken.objects.update_or_create(
        user=request.user, token=generate_numeric_token
    )
    email_context = {
        "org_long_name": settings.ORG_LONG_NAME,
        "org_email": settings.ORG_EMAIL,
        "org_short_name": settings.ORG_SHORT_NAME,
        "token": token_obj.token,
        "username": request.user.email,
        "site": Site.find_for_request(request),
        "user": request.user,
        "timeout_minutes": settings.PASSWORDLESS_LOGIN_TIMEOUT // 60,
    }
    subject = "Confirmation code for {org_long_name}: {token}".format(**email_context)
    email = MarkdownMail("users/emails/confirm_access.md")
    email.send(
        to=request.user.email,
        subject=subject,
        from_email=settings.DEFAULT_FROM_EMAIL,
        context=email_context,
    )
    return render(
        request,
        "users/partials/confirmation_code_sent.html",
        {"redirect_url": get_redirect_url(request, "next")},
    )


@never_cache
@login_required
@ratelimit(key="user", rate=settings.DEFAULT_RATE_LIMIT)
def elevate_check_code_view(request):
    """Checks if the code is correct and if so, elevates the user session."""
    token = request.POST.get("code")

    def validate_token_and_age(token):
        try:
            token_obj = ConfirmAccessToken.objects.get(user=request.user, token=token)
            token_age_in_seconds = (timezone.now() - token_obj.modified).total_seconds()
            if token_age_in_seconds <= settings.PASSWORDLESS_LOGIN_TIMEOUT:
                token_obj.delete()
                return True
        except ConfirmAccessToken.DoesNotExist:
            return False

    redirect_url = get_redirect_url(request, "next")
    if token and validate_token_and_age(token):
        grant_elevated_privileges(request)
        return HttpResponseClientRedirect(redirect_url)

    return render(
        request,
        "users/partials/confirmation_code_sent.html",
        {"error": True, "redirect_url": redirect_url},
    )


@login_required
def set_password_view(request):
    """Sends email with link to set password to user that doesn't have usable password.

    This will the case when the user signed up using passwordless signup or using oauth.
    """
    site = Site.find_for_request(request)

    if not request.user.has_usable_password():
        send_activation_email(
            user=request.user,
            site=site,
            email_template="users/emails/set_password.txt",
            email_subject_template="users/emails/set_password_subject.txt",
        )
        return HttpResponse("✓ Check your email for password set link.")
