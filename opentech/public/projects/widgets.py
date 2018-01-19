import json

from django import forms

from opentech.apply.categories.models import Category


class LazyChoices:
    def __init__(self, queryset, display):
        self.queryset = queryset
        self.display = display

    def __iter__(self):
        for choice in self.queryset.values_list(*self.display):
            yield choice


class LazyWidgets:
    def __init__(self, widget, model):
        self.model = model
        self.widget = widget

    def __iter__(self):
        for obj in self.model.objects.order_by('id'):
            yield self.widget(
                attrs={'id': obj.id, 'label_tag': obj.name},
                choices=LazyChoices(obj.options, ['id', 'value']),
            )


class OptionsWidget(forms.CheckboxSelectMultiple):
    template_name = 'projects/widgets/options_widget.html'
    option_template_name = 'projects/widgets/options_option.html'

    def __init__(self, *args, **kwargs):
        choices = kwargs['choices']
        super().__init__(*args, **kwargs)
        self.choices = choices


class CategoriesWidget(forms.MultiWidget):
    template_name = 'projects/widgets/categories_widget.html'

    def __init__(self, *args, **kwargs):
        kwargs['widgets'] = list()
        super().__init__(*args, **kwargs)
        self.widgets = LazyWidgets(OptionsWidget, Category)

    def decompress(self, value):
        data = json.loads(value)
        return [
            data.get(str(widget.attrs['id']), list()) for widget in self.widgets
        ]

    def value_from_datadict(self, data, files, name):
        data = {
            widget.attrs['id']: widget.value_from_datadict(data, files, name + '_%s' % i)
            for i, widget in enumerate(self.widgets)
        }
        return json.dumps(data)

    def get_context(self, *args, **kwargs):
        context = super().get_context(*args, **kwargs)
        # Mutliwidget kills the wrap_label option when it is building the context
        context['wrap_label'] = True
        return context
