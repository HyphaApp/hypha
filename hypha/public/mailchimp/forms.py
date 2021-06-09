from django import forms
from django.utils.translation import gettext_lazy as _


class NewsletterForm(forms.Form):
    email = forms.EmailField(label=_('Email Address'))
    fname = forms.CharField(label=_('First Name'), required=False)
    lname = forms.CharField(label=_('Last Name'), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            class_name = 'input--secondary'
            if field.required:
                class_name += ' input__secondary--required'
            field.widget.attrs = {'class': class_name}
