from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _
from django_select2.forms import Select2Widget
from wagtail.core.models import Site
from wagtail.users.forms import UserCreationForm, UserEditForm

from .models import UserSettings

User = get_user_model()


class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.site = Site.find_for_request(self.request)
        self.user_settings = UserSettings.for_site(site=self.site)
        self.extra_text = self.user_settings.extra_text
        if self.user_settings.consent_show:
            self.fields['consent'] = forms.BooleanField(
                label=self.user_settings.consent_text,
                help_text=self.user_settings.consent_help,
                required=True,
            )


class CustomUserAdminFormBase():
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # HACK: Wagtail admin doesn't work with custom User models that do not have first/last name.
        self.fields['first_name'].widget = forms.HiddenInput(attrs={'value': 'Not used - see full_name'})
        self.fields['last_name'].widget = forms.HiddenInput(attrs={'value': 'Not used - see full_name'})


class CustomUserEditForm(CustomUserAdminFormBase, UserEditForm):
    pass


class CustomUserCreationForm(CustomUserAdminFormBase, UserCreationForm):
    pass


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['full_name', 'email', 'slack']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.is_apply_staff:
            del self.fields['slack']

        if not self.instance.has_usable_password():
            # User is registered with oauth - no password change allowed
            email_field = self.fields['email']
            email_field.disabled = True
            email_field.required = False
            email_field.help_text = _('You are registered using OAuth, please contact an admin if you need to change your email address.')

    def clean_slack(self):
        slack = self.cleaned_data['slack']
        if slack:
            slack = slack.strip()
            if ' ' in slack:
                raise forms.ValidationError('Slack names must not include spaces')

            if not slack.startswith('@'):
                slack = '@' + slack

        return slack


class BecomeUserForm(forms.Form):
    user_pk = forms.ModelChoiceField(
        widget=Select2Widget,
        help_text=_('Only includes active, non-superusers'),
        queryset=User.objects.filter(is_active=True, is_superuser=False),
        label='',
        required=False,
    )


class EmailChangePasswordForm(forms.Form):
    password = forms.CharField(
        label=_("Password"),
        help_text=_("Email change requires you to put password."),
        strip=False,
        widget=forms.PasswordInput(attrs={'autofocus': True}),
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_password(self):
        password = self.cleaned_data["password"]
        if not self.user.check_password(password):
            raise forms.ValidationError(
                _("Incorrect password. Please try again."),
                code='password_incorrect',
            )
        return password

    def save(self, updated_email, name, slack, commit=True):
        self.user.full_name = name
        self.user.slack = slack
        if commit:
            self.user.save()
        return self.user


class TWOFAPasswordForm(forms.Form):
    password = forms.CharField(
        label=_("Please type your password to confirm"),
        strip=False,
        widget=forms.PasswordInput(attrs={'autofocus': True}),
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_password(self):
        password = self.cleaned_data["password"]
        if not self.user.check_password(password):
            raise forms.ValidationError(
                _("Incorrect password. Please try again."),
                code='password_incorrect',
            )
        return password
