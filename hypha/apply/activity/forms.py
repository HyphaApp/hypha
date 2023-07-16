from django import forms
from django.core.exceptions import ValidationError
from pagedown.widgets import PagedownWidget

from .models import Activity


class CommentForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = ('message', 'visibility')
        labels = {
            'visibility': 'Visible to',
            'message': 'Message',
        }
        help_texts = {
            'visibility': 'Pick a suitable user role. Staff can view every comment.'
        }
        widgets = {
            'visibility': forms.RadioSelect(),
            'message': PagedownWidget(),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.visibility_choices = self._meta.model.visibility_choices_for(user)
        visibility = self.fields['visibility']
        # Set default visibility to "Applicant" for staff and staff can view everything.
        visibility.initial = self.visibility_choices[0]
        if len(self.visibility_choices) > 1:
            visibility.choices = self.visibility_choices
        else:
            visibility.required = False
            visibility.choices = self.visibility_choices
            visibility.initial = visibility.initial[0]
            visibility.widget = forms.HiddenInput()
