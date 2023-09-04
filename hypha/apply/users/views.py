import datetime
from typing import Any
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login, update_session_auth_hash
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.forms import AdminPasswordChangeForm
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth.views import (
    INTERNAL_RESET_SESSION_TOKEN,
    SuccessURLAllowedHostsMixin,
)
from django.contrib.auth.views import (
    PasswordResetConfirmView as DjPasswordResetConfirmView,
)
from django.contrib.auth.views import PasswordResetView as DjPasswordResetView
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import PermissionDenied
from django.core.signing import BadSignature, Signer, TimestampSigner, dumps, loads
from django.http import HttpResponseRedirect
from django.shortcuts import Http404, get_object_or_404, redirect, render, resolve_url
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import UpdateView
from django.views.generic.base import TemplateView, View
from django.views.generic.edit import FormView
from django_otp import devices_for_user
from django_ratelimit.decorators import ratelimit
from elevate.mixins import ElevateMixin
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

from hypha.apply.home.models import ApplyHomePage

from .decorators import require_oauth_whitelist
from .forms import (
    BecomeUserForm,
    CustomAuthenticationForm,
    CustomUserCreationForm,
    EmailChangePasswordForm,
    ProfileForm,
    TWOFAPasswordForm,
)
from .utils import get_redirect_url, send_confirmation_email

User = get_user_model()


@method_decorator(
    ratelimit(key="ip", rate=settings.DEFAULT_RATE_LIMIT, method="POST"),
    name="dispatch",
)
class RegisterView(SuccessURLAllowedHostsMixin, View):
    redirect_field_name = "next"
    form = CustomUserCreationForm

    def get(self, request):
        # We keep /register in the urls in order to test (where we turn on/off
        # the setting per test), but when disabled, we want to pretend it doesn't
        # exist va 404
        if not settings.ENABLE_REGISTRATION_WITHOUT_APPLICATION:
            raise Http404

        if request.user.is_authenticated:
            return redirect("dashboard:dashboard")

        ctx = {
            "form": self.form(),
            "redirect_url": get_redirect_url(request, self.redirect_field_name),
        }
        return render(request, "users/register.html", ctx)

    def post(self, request):
        # See comment in get() above about doing this here rather than in urls
        if not settings.ENABLE_REGISTRATION_WITHOUT_APPLICATION:
            raise Http404

        form = self.form(data=request.POST)
        context = {}
        if form.is_valid():
            # If using wagtail password management
            if "password1" in form.cleaned_data:
                context["password"] = form.cleaned_data["password1"]

            site = Site.find_for_request(self.request)
            user, created = User.objects.get_or_create_and_notify(
                email=form.cleaned_data["email"],
                site=site,
                redirect_url=get_redirect_url(request, self.redirect_field_name),
                defaults={
                    "full_name": form.cleaned_data["full_name"],
                },
                **context,
            )
            if created:
                params = {"name": user.full_name, "email": user.email}
                # redirect to success page with params as query params
                return HttpResponseRedirect(
                    resolve_url("users_public:register-success")
                    + "?"
                    + urlencode(params)
                )
        return render(request, "users/register.html", {"form": form})


class RegistrationSuccessView(TemplateView):
    template_name = "users/register-success.html"


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

    def form_valid(self, form):
        updated_email = form.cleaned_data["email"]
        name = form.cleaned_data["full_name"]
        slack = form.cleaned_data.get("slack", "")
        user = get_object_or_404(User, id=self.request.user.id)
        if updated_email:
            base_url = reverse("users:email_change_confirm_password")
            query_dict = {"updated_email": updated_email, "name": name, "slack": slack}

            signer = TimestampSigner()
            signed_value = signer.sign(dumps(query_dict))
            # Using session variables for redirect validation
            token_signer = Signer()
            self.request.session["signed_token"] = token_signer.sign(user.email)
            return redirect(
                "{}?{}".format(base_url, urlencode({"value": signed_value}))
            )
        return super(AccountView, self).form_valid(form)

    def get_success_url(
        self,
    ):
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


@method_decorator(login_required, name="dispatch")
class EmailChangePasswordView(FormView):
    form_class = EmailChangePasswordForm
    template_name = "users/email_change/confirm_password.html"
    success_url = reverse_lazy("users:confirm_link_sent")
    title = _("Enter Password")

    def get_initial(self):
        """
        Validating the redirection from account via session variable
        """
        if "signed_token" not in self.request.session:
            raise Http404
        signer = Signer()
        try:
            signer.unsign(self.request.session["signed_token"])
        except BadSignature as e:
            raise Http404 from e
        return super(EmailChangePasswordView, self).get_initial()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        # Make sure redirection url is inaccessible after email is sent
        if "signed_token" in self.request.session:
            del self.request.session["signed_token"]
        signer = TimestampSigner()
        try:
            unsigned_value = signer.unsign(
                self.request.GET.get("value"), max_age=settings.PASSWORD_PAGE_TIMEOUT
            )
        except Exception:
            messages.error(
                self.request,
                _("Password Page timed out. Try changing the email again."),
            )
            return redirect("users:account")
        value = loads(unsigned_value)
        form.save(**value)
        user = self.request.user
        if user.email != value["updated_email"]:
            send_confirmation_email(
                user,
                signer.sign(dumps(value["updated_email"])),
                updated_email=value["updated_email"],
                site=Site.find_for_request(self.request),
            )
        # alert email
        user.email_user(
            subject="Alert! An attempt to update your email.",
            message=render_to_string(
                "users/email_change/update_info_email.html",
                {
                    "name": user.get_full_name(),
                    "username": user.get_username(),
                    "org_email": settings.ORG_EMAIL,
                    "org_short_name": settings.ORG_SHORT_NAME,
                    "org_long_name": settings.ORG_LONG_NAME,
                },
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
        )
        return super(EmailChangePasswordView, self).form_valid(form)


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


class ActivationView(SuccessURLAllowedHostsMixin, TemplateView):
    redirect_field_name = "next"

    def get(self, request, *args, **kwargs):
        user = self.get_user(kwargs.get("uidb64"))

        if self.valid(user, kwargs.get("token")):
            user.backend = settings.CUSTOM_AUTH_BACKEND
            login(request, user)
            if (
                settings.WAGTAILUSERS_PASSWORD_ENABLED
                and settings.ENABLE_REGISTRATION_WITHOUT_APPLICATION
            ):
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
class TWOFADisableView(TwoFactorDisableView):
    """
    View for disabling two-factor for a user's account.
    """

    template_name = "two_factor/profile/disable.html"
    success_url = reverse_lazy("users:account")
    form_class = TWOFAPasswordForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


@method_decorator(
    permission_required(change_user_perm, raise_exception=True), name="dispatch"
)
class TWOFAAdminDisableView(FormView):
    """
    View for PasswordForm to confirm the Disable 2FA process on wagtail admin.
    """

    form_class = TWOFAPasswordForm
    template_name = "two_factor/admin/disable.html"
    user = None

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # pass request's user to form to validate the password
        kwargs["user"] = self.request.user
        # store the user from url for redirecting to the same user's account edit page
        self.user = get_object_or_404(User, pk=self.kwargs.get("user_id"))
        return kwargs

    def get_form(self, form_class=None):
        form = super(TWOFAAdminDisableView, self).get_form(form_class=form_class)
        form.fields["password"].label = "Password"
        return form

    def form_valid(self, form):
        for device in devices_for_user(self.user):
            device.delete()
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("wagtailusers_users:edit", args=[self.user.id])

    def get_context_data(self, **kwargs):
        ctx = super(TWOFAAdminDisableView, self).get_context_data(**kwargs)
        ctx["user"] = self.user
        return ctx


class TWOFARequiredMessageView(TemplateView):
    template_name = "two_factor/core/two_factor_required.html"


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
