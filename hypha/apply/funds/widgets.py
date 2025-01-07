from django import forms


class MultiCheckboxesWidget(forms.SelectMultiple):
    """
    Custom widget for Choices.js. Adds the required attributes.
    """

    def __init__(self, *args, **kwargs):
        attrs = kwargs.get("attrs", {})
        # Add the class for Choices.js initialization
        attrs.setdefault("class", "js-choices")
        attrs.setdefault("data-placeholder", "")
        kwargs["attrs"] = attrs
        super().__init__(*args, **kwargs)


class MetaTermWidget(forms.SelectMultiple):
    def create_option(
        self, name, value, label, selected, index, subindex=None, attrs=None
    ):
        disabled = False

        if isinstance(label, dict):
            label, disabled = label.get("label"), label.get("disabled")

        option_dict = super().create_option(
            name, value, label, selected, index, subindex=subindex, attrs=attrs
        )

        if disabled:
            option_dict["attrs"]["disabled"] = "disabled"
        return option_dict
