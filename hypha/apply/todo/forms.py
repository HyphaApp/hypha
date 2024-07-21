from django import forms

from .models import Task


class TaskCreateForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = (
            "code",
            "user",
            "user_group",
        )
