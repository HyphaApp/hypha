from django import forms

from .models import Activity


class CommentForm(forms.ModelForm):
    visibility = forms.BooleanField(label='Internal')

    class Meta:
        model = Activity
        fields = ('message', 'visibility')

    # def clean(self):
