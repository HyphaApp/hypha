from django import forms
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe

from pagedown.widgets import PagedownWidget

from .models import Activity, VISIBILILTY_HELP_TEXT, VISIBILITY


class CommentForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = ('message', 'visibility')
        labels = {
            'visibility': 'Visible to',
            'message': '',
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
        visibility.initial = self.visibility_choices[0]
        if len(self.visibility_choices) > 1:
            visibility.choices = self.visibility_choices
            visibility.help_text = mark_safe('<br>'.join(
                [VISIBILITY[choice] + ': ' + VISIBILILTY_HELP_TEXT[choice] for choice in self.allowed_visibility]
            ))
        else:
            visibility.widget = forms.HiddenInput()

    def clean_visibility(self):
        choice = self.cleaned_data['visibility']
        if choice not in self.allowed_visibility:
            raise ValidationError('You do not have permission for that visibility.')
        return choice
