from django import forms
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailusers.forms import UserEditForm, UserCreationForm


class CustomUserEditForm(UserEditForm):
    full_name = forms.CharField(label=_("Full name"), required=False, help_text=_("Leave blank to generate from First and Last name values."))


class CustomUserCreationForm(UserCreationForm):
    full_name = forms.CharField(label=_("Full name"), required=False, help_text=_("Leave blank to generate from First and Last name values."))
