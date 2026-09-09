from django import forms


class ChoicesJSMixin:
    """
    Adds the attributes required to initialise Choices.js on a select.
    """

    def __init__(self, attrs=None, *args, **kwargs):
        attrs = dict(attrs) if attrs else {}
        # Add the data attributes for Choices.js initialization
        attrs.setdefault("data-js-choices", "")
        attrs.setdefault("data-placeholder", "")
        super().__init__(attrs, *args, **kwargs)

    def use_required_attribute(self, initial):
        # Choices.js conceals the underlying <select>, and browsers refuse to
        # submit a form with a hidden required control, without showing the user
        # an error. Required is still enforced server side by the form field.
        return False


class ChoicesSelectWidget(ChoicesJSMixin, forms.Select):
    pass


class ChoicesSelectMultipleWidget(ChoicesJSMixin, forms.SelectMultiple):
    pass
