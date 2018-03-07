from django import forms

from .models import Activity


class CommentForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = ('message', 'visibility')
        labels = {
            'visibility': '',
        }
        widgets = {
            'visibility': forms.RadioSelect(),
        }
