from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _
from django_select2.forms import Select2Widget
from wagtail.users.forms import UserCreationForm, UserEditForm

from .models import AuthSettings

User = get_user_model()


class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_settings = AuthSettings.load(request_or_site=self.request)
        self.extra_text = self.user_settings.extra_text
        if self.user_settings.consent_show:
            self.fields["consent"] = forms.BooleanField(
                label=self.user_settings.consent_text,
                help_text=self.user_settings.consent_help,
                required=True,
            )


class PasswordlessAuthForm(forms.Form):
    """Form to collect the email for passwordless login or signup (if enabled)

    Adds login extra text and user content to the form, if configured in the
    wagtail auth settings.
    """

    email = forms.EmailField(
        label=_("Email Address"),
        required=True,
        max_length=254,
        widget=forms.EmailInput(attrs={"autofocus": True, "autocomplete": "email"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = kwargs.pop("request", None)
        self.user_settings = AuthSettings.load(request_or_site=self.request)
        self.extra_text = self.user_settings.extra_text
        if self.user_settings.consent_show:
            self.fields["consent"] = forms.BooleanField(
                label=self.user_settings.consent_text,
                help_text=self.user_settings.consent_help,
                required=True,
            )


class CustomUserAdminFormBase:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # HACK: Wagtail admin doesn't work with custom User models that do not have first/last name.
        self.fields["first_name"].widget = forms.HiddenInput(
            attrs={"value": "Not used - see full_name"}
        )
        self.fields["last_name"].widget = forms.HiddenInput(
            attrs={"value": "Not used - see full_name"}
        )


class CustomUserEditForm(CustomUserAdminFormBase, UserEditForm):
    pass


class CustomUserCreationForm(CustomUserAdminFormBase, UserCreationForm):
    error_messages = {
        "duplicate_username": _("A user with that email already exists."),
        "password_mismatch": _("The two password fields didn't match."),
    }

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)

        self.user_settings = AuthSettings.load(request_or_site=self.request)
        if self.user_settings.consent_show:
            self.fields["consent"] = forms.BooleanField(
                label=self.user_settings.consent_text,
                help_text=self.user_settings.consent_help,
                required=True,
            )


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["full_name", "email", "slack"]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
        if not self.instance.is_apply_staff_or_finance:
            del self.fields["slack"]

        if self.request is not None:
            backend = self.request.session["_auth_user_backend"]
            if "social_core.backends" in backend:
                # User is registered with oauth - no password change allowed
                email_field = self.fields["email"]
                email_field.disabled = True
                email_field.required = False
                email_field.help_text = _(
                    "You are registered using OAuth, please contact an admin if you need to change your email address."
                )

    def clean_slack(self):
        slack = self.cleaned_data["slack"]
        if slack:
            slack = slack.strip()
            if " " in slack:
                raise forms.ValidationError("Slack names must not include spaces")

            if not slack.startswith("@"):
                slack = "@" + slack

        return slack

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            email = (
                self.instance.email
            )  # updated email to avoid email existing message, fix information leak.
        return email


class BecomeUserForm(forms.Form):
    user_pk = forms.ModelChoiceField(
        widget=Select2Widget,
        help_text=_("Only includes active, non-superusers"),
        queryset=User.objects.filter(is_active=True, is_superuser=False),
        label="",
        required=False,
    )


class EmailChangePasswordForm(forms.Form):
    password = forms.CharField(
        label=_("Password"),
        help_text=_("Email change requires you to put password."),
        strip=False,
        widget=forms.PasswordInput(attrs={"autofocus": True}),
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_password(self):
        password = self.cleaned_data["password"]
        if not self.user.check_password(password):
            raise forms.ValidationError(
                _("Incorrect password. Please try again."),
                code="password_incorrect",
            )
        return password

    def save(self, updated_email, name, slack, commit=True):
        self.user.full_name = name
        if slack is not None:
            self.user.slack = slack
        if commit:
            self.user.save()
        return self.user


class TWOFAPasswordForm(forms.Form):
    password = forms.CharField(
        label=_("Please type your password to confirm"),
        strip=False,
        widget=forms.PasswordInput(attrs={"autofocus": True}),
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_password(self):
        password = self.cleaned_data["password"]
        if not self.user.check_password(password):
            raise forms.ValidationError(
                _("Incorrect password. Please try again."),
                code="password_incorrect",
            )
        return password
