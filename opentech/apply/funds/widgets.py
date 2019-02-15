from django.contrib.staticfiles.templatetags.staticfiles import static

from django_select2.forms import Select2Widget, Select2MultipleWidget


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


class Select2IconWidget(Select2Widget):
    template_name = 'funds/widgets/icon_select2.html'

    def __init__(self, *args, **kwargs):
        attrs = kwargs.get('attrs', {})
        attrs.setdefault('icon', '')
        kwargs['attrs'] = attrs
        super().__init__(*args, **kwargs)
