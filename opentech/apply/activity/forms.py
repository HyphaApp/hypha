from django import forms

from .models import Activity


class CommentForm(forms.ModelForm):
    internal = forms.BooleanField()

    class Meta:
        model = Activity
        fields = ('message',)

    def save(self):
        self.instance.visibility
