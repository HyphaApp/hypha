from django import forms

from django_countries.widgets import CountrySelectWidget
from django_countries import countries


class KeepOwnAttrsWidget(forms.Widget):
    def get_context(self, name, value, attrs):
        attrs.update(self.attrs)
        return super().get_context(name, value, attrs)


class CountrySelectWithChoices(KeepOwnAttrsWidget, CountrySelectWidget):
    def __init__(self, *args, **kwargs):
        kwargs['choices'] = countries
        super().__init__(*args, **kwargs)


class KeepAttrsTextInput(KeepOwnAttrsWidget, forms.TextInput):
    pass


class NestedMultiWidget(KeepOwnAttrsWidget, forms.MultiWidget):
    template_name = 'addressfield/widgets/nested_with_label.html'

    def __init__(self, *args, **kwargs):
        widgets = [
            widget(attrs={'class': field, 'required': False}) for field, widget in self.components.items()
        ]
        super().__init__(widgets, *args, **kwargs)

    @property
    def field_names(self):
        return list(self.components.keys())

    def decompress(self, value):
        if value:
            decompressed = list()
            for i, widget in enumerate(self.widgets):
                if hasattr(widget, 'components'):
                    decompressed.append(widget.decompress(value))
                else:
                    decompressed.append(value.get(self.field_names[i]))
            return decompressed
        return [None] * len(self.components)

    def value_from_datadict(self, data, files, name):
        value = dict()
        for i, widget in enumerate(self.widgets):
            widget_value = widget.value_from_datadict(data, files, name + '_%s' % i)
            # flatten the data structure to a single dict
            if hasattr(widget, 'widgets'):
                value.update(widget_value)
            else:
                value[self.field_names[i]] = widget_value
        return value

class LocalityWidget(NestedMultiWidget):
    components = {
        'localityname': KeepAttrsTextInput,
        'administrativearea': KeepAttrsTextInput,
        'postalcode': KeepAttrsTextInput,
    }


class AddressWidget(NestedMultiWidget):
    components = {
        'country': CountrySelectWithChoices,
        'thoroughfare': KeepAttrsTextInput,
        'premise': KeepAttrsTextInput,
        'locality': LocalityWidget,
    }

    class Media:
        js = (
            'https://cdn.jsdelivr.net/npm/jquery.addressfield@1.1.0/dist/jquery.addressfield.js',
            # 'jquery.addressfield.min.js',
            'address_form.js',
            )

    def __init__(self, *args, **kwargs):
        attrs = kwargs.get('attrs', dict())
        attrs['class'] = 'address'
        kwargs['attrs'] = attrs
        super().__init__(*args, **kwargs)
