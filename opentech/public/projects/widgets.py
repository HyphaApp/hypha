import json

from django import forms

from opentech.apply.categories.models import Category


class OptionsWidget(forms.CheckboxSelectMultiple):
    template_name = 'projects/widgets/options_widget.html'
    option_template_name = 'projects/widgets/options_option.html'

class CategoriesWidget(forms.MultiWidget):
    template_name = 'projects/widgets/categories_widget.html'

    def __init__(self, *args, **kwargs):
        widgets = [
            OptionsWidget(
                attrs={'id': cat.id, 'label_tag': cat.name},
                choices=cat.options.all().values_list('id', 'value'),
            )
            for cat in Category.objects.all()
        ]
        kwargs['widgets'] = widgets
        super().__init__(*args, **kwargs)

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
