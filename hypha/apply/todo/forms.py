from django import forms

from .models import Task


class TaskCreateForm(forms.ModelForm):
    assigned_to = forms.ChoiceField(
        choices=(("user", "Single User"), ("user_group", "User Groups"))
    )
    msg = forms.CharField(max_length=120)
    related_obj = forms.ChoiceField(choices=())
    type = forms.CharField(empty_value="manual", widget=forms.HiddenInput())

    class Meta:
        model = Task
        fields = (
            "code",
            "assigned_to",
            "user",
            "user_group",
            "msg",
            "related_obj",
            "type",
        )
