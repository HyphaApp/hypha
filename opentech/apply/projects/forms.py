from django import forms


class CreateProjectForm(forms.Form):
    submission = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, instance=None, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if instance:
            self.fields['submission'].initial = instance.id
