from django import forms
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailusers.forms import UserEditForm, UserCreationForm


class CustomUserEditForm(UserEditForm):
    full_name = forms.CharField(label=_("Full name"), required=True)

    def __init__(self, *args, **kwargs):
        super(CustomUserEditForm, self).__init__(*args, **kwargs)

        # HACK: Wagtail admin doesn't work with custom User models that do not have first/last name.
        self.fields['first_name'].widget = forms.HiddenInput(attrs={'value': f"fn{self.instance.pk}"})
        self.fields['last_name'].widget = forms.HiddenInput(attrs={'value': f"ln{self.instance.pk}"})


class CustomUserCreationForm(UserCreationForm):
    full_name = forms.CharField(label=_("Full name"), required=True)

    def __init__(self, *args, **kwargs):
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)

        # HACK: Wagtail admin doesn't work with custom User models that do not have first/last name.
        self.fields['first_name'].widget = forms.HiddenInput(attrs={'value': f"fn{self.instance.pk}"})
        self.fields['last_name'].widget = forms.HiddenInput(attrs={'value': f"ln{self.instance.pk}"})
