from django import forms

from wagtail.users.forms import UserEditForm, UserCreationForm


class CustomUserAdminFormBase():
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # HACK: Wagtail admin doesn't work with custom User models that do not have first/last name.
        self.fields['first_name'].widget = forms.HiddenInput(attrs={'value': f"Not used - see full_name"})
        self.fields['last_name'].widget = forms.HiddenInput(attrs={'value': f"Not used - see full_name"})


class CustomUserEditForm(CustomUserAdminFormBase, UserEditForm):
    pass


class CustomUserCreationForm(CustomUserAdminFormBase, UserCreationForm):
    pass
