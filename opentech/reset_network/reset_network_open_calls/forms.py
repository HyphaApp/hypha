from django import forms


class ResetNetworkOpenCallsForm(forms.Form):
    name = forms.CharField(max_length=255, required=True)
    email = forms.EmailField(max_length=255, required=True)
