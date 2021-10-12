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
        widgets = {
            'visibility': forms.RadioSelect(),
            'message': PagedownWidget(),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.allowed_visibility = self._meta.model.visibility_for(user)
        self.visibility_choices = self._meta.model.visibility_choices_for(user)
        visibility = self.fields['visibility']
        # Set default visibility to "team" for staff and to "applicant" for everyone else.
        visibility.initial = self.visibility_choices[1] if user.is_apply_staff else self.visibility_choices[0]
        if len(self.visibility_choices) > 1:
            visibility.choices = self.visibility_choices
        else:
            visibility.widget = forms.HiddenInput()

    def clean_visibility(self):
        choice = self.cleaned_data['visibility']
        if choice not in self.allowed_visibility:
            raise ValidationError('You do not have permission for that visibility.')
        return choice
