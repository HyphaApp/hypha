from django.contrib.staticfiles.templatetags.staticfiles import static

from django_select2.forms import Select2MultipleWidget


class Select2MultiCheckboxesWidget(Select2MultipleWidget):
    class Media:
        js = (
            static('js/select2.multi-checkboxes.js'),
            static('js/django_select2-checkboxes.js'),
        )

    def __init__(self, *args, **kwargs):
        attrs = kwargs.get('attrs', {})
        attrs.setdefault('data-placeholder', 'items')
        kwargs['attrs'] = attrs
        super().__init__(*args, **kwargs)

    def build_attrs(self, *args, **kwargs):
        attrs = super().build_attrs(*args, **kwargs)
        attrs['class'] = attrs['class'].replace('django-select2', 'django-select2-checkboxes')
        return attrs


class MetaTermSelect2Widget(Select2MultipleWidget):

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        disabled = False

        if isinstance(label, dict):
            label, disabled = label.get('label'), label.get('disabled')

        option_dict = super().create_option(
            name, value, label, selected, index, subindex=subindex, attrs=attrs
        )

        if disabled:
            option_dict['attrs']['disabled'] = 'disabled'
        return option_dict
