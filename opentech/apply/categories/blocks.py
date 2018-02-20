from django import forms
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailcore.blocks import BooleanBlock, CharBlock, ChooserBlock, TextBlock
from wagtail.wagtailcore.utils import resolve_model_string

from opentech.apply.stream_forms.blocks import OptionalFormFieldBlock


class ModelChooserBlock(ChooserBlock):
    widget = forms.Select

    def __init__(self, target_model, **kwargs):
        self._target_model = target_model
        super().__init__(**kwargs)

    @cached_property
    def target_model(self):
        return resolve_model_string(self._target_model)


class CategoryQuestionBlock(OptionalFormFieldBlock):
    class Meta:
        template = 'stream_forms/render_list_field.html'

    # Overwrite field label and help text so we can defer to the category
    # as required
    field_label = CharBlock(
        label=_('Label'),
        required=False,
        help_text=_('Leave blank to use the default Category label'),
    )
    help_text = TextBlock(
        required=False,
        label=_('Leave blank to use the default Category help text'),
    )
    category = ModelChooserBlock('categories.Category')
    multi = BooleanBlock(label='Multi select', required=False)

    def get_field_class(self, struct_value):
        if struct_value['multi']:
            return forms.MultipleChoiceField
        else:
            return forms.ChoiceField

    def use_defaults_from_category(self, kwargs, category):
        category_fields = {'label': 'name', 'help_text': 'help_text'}

        for field in category_fields.keys():
            if not kwargs.get(field):
                kwargs[field] = getattr(category, category_fields[field])

        return kwargs

    def get_field_kwargs(self, struct_value):
        kwargs = super().get_field_kwargs(struct_value)
        category = struct_value['category']
        kwargs = self.use_defaults_from_category(kwargs, category)
        choices = category.options.values_list('id', 'value')
        kwargs.update({'choices': choices})
        return kwargs

    def get_widget(self, struct_value):
        if struct_value['multi']:
            return forms.CheckboxSelectMultiple
        else:
            return forms.RadioSelect

    def render(self, value, context):
        data = context['data']
        category = value['category']
        context['data'] = category.options.filter(id__in=data).values_list('value', flat=True)
        return super().render(value, context)
