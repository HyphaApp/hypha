from django import forms
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailusers.forms import UserEditForm, UserCreationForm


class CustomUserEditForm(UserEditForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # HACK: Wagtail admin doesn't work with custom User models that do not have first/last name.
        self.fields['first_name'].widget = forms.HiddenInput(attrs={'value': f"Not used - see full_name"})
        self.fields['last_name'].widget = forms.HiddenInput(attrs={'value': f"Not used - see full_name"})

class CustomUserCreationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # HACK: Wagtail admin doesn't work with custom User models that do not have first/last name.
        self.fields['first_name'].widget = forms.HiddenInput(attrs={'value': f"Not used - see full_name"})
        self.fields['last_name'].widget = forms.HiddenInput(attrs={'value': f"Not used - see full_name"})
