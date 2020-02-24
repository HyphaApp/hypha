from django import forms


class NewsletterForm(forms.Form):
    email = forms.EmailField(label='Email Address')
    fname = forms.CharField(label='First Name', required=False)
    lname = forms.CharField(label='Last Name', required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            class_name = 'input--secondary'
            if field.required:
                class_name += ' input__secondary--required'
            field.widget.attrs = {'class': class_name}
