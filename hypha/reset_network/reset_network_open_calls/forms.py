from django import forms


class ResetNetworkOpenCallsForm(forms.Form):
    name = forms.CharField(max_length=255, required=True, widget=forms.TextInput({"placeholder": "Your name"}))
    email = forms.EmailField(max_length=255, required=True, widget=forms.TextInput({"placeholder": "Your email"}))
    confirm = forms.BooleanField(required=True, help_text="Help text")
