from django import forms


class ChoicesJSMixin:
    """
    Adds the attributes required to initialise Choices.js on a select.
    """

    def __init__(self, *args, **kwargs):
        attrs = kwargs.get("attrs", {})
        # Add the data attributes for Choices.js initialization
        attrs.setdefault("data-js-choices", "")
        attrs.setdefault("data-placeholder", "")
        kwargs["attrs"] = attrs
        super().__init__(*args, **kwargs)


class ChoicesSelectWidget(ChoicesJSMixin, forms.Select):
    pass


class ChoicesSelectMultipleWidget(ChoicesJSMixin, forms.SelectMultiple):
    pass
