from typing import Any, Iterable, Literal, Optional

from argostranslate.package import Package
from django import forms


class LanguageChoiceField(forms.ChoiceField):
    def __init__(
        self,
        role: Literal["to", "from"],
        available_packages: Iterable[Package],
        choices: Optional[Iterable[str]] = set(),
        **kwargs,
    ) -> None:
        self.available_packages = available_packages

        # Ensure the given language is either "to" or "from"
        if role not in ["to", "from"]:
            raise ValueError(f'Invalid role "{role}", must be "to" or "from"')

        self.role = role

        super().__init__(choices=choices, **kwargs)
        self.widget.attrs.update({"data-placeholder": f"{role.capitalize()}..."})

    def validate(self, value: Any) -> None:
        """Basic validation to ensure the language (depending on role) is available in the installed packages

        Only checks the language exists as from/to code, doesn't validate based on from -> to.
        """
        if self.role == "from":
            valid_list = [package.from_code for package in self.available_packages]
        else:
            valid_list = [package.to_code for package in self.available_packages]

        if value not in valid_list:
            raise forms.ValidationError(
                "The specified language is either invalid or not installed"
            )
