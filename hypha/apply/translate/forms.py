from django import forms

from hypha.apply.translate.fields import LanguageChoiceField
from hypha.apply.translate.utils import get_available_translations


class TranslateSubmissionForm(forms.Form):
    available_packages = get_available_translations()

    from_lang = LanguageChoiceField("from", available_packages)
    to_lang = LanguageChoiceField("to", available_packages)

    def clean(self):
        form_data = self.cleaned_data
        try:
            from_code = form_data["from_lang"]
            to_code = form_data["to_lang"]

            to_packages = get_available_translations([from_code])

            if to_code not in [package.to_code for package in to_packages]:
                self.add_error(
                    "to_lang",
                    "The specified language is either invalid or not installed",
                )

            return form_data
        except KeyError as err:
            # If one of the fields could not be parsed, there is likely bad input being given
            raise forms.ValidationError("Invalid input selected") from err
