from django import forms
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django_select2.forms import Select2MultipleWidget
from wagtail.blocks import BooleanBlock, CharBlock, ChoiceBlock, TextBlock
from wagtail.coreutils import resolve_model_string

from hypha.apply.stream_forms.blocks import OptionalFormFieldBlock


class ModelChooserBlock(ChoiceBlock):
    # Implement this block as it's referenced in the old migrations.
    pass


def get_categories_as_choices():
    Category = resolve_model_string("categories.Category")
    return [(cat.id, cat.name) for cat in Category.objects.all()]


class CategoryQuestionBlock(OptionalFormFieldBlock):
    class Meta:
        template = "stream_forms/render_list_field.html"

    category = ModelChooserBlock(required=True, choices=get_categories_as_choices)
    multi = BooleanBlock(label=_("Multi select"), required=False)
    # Overwrite field label and help text so we can defer to the category
    # as required
    field_label = CharBlock(
        label=_("Label"),
        required=False,
        help_text=_("Leave blank to use the default Category label"),
    )
    help_text = TextBlock(
        label=_("Help text"),
        required=False,
        help_text=_("Leave blank to use the default Category help text"),
    )

    @cached_property
    def model_class(self):
        return resolve_model_string("categories.Category")

    def get_instance(self, id):
        return self.model_class.objects.get(id=id)

    def get_field_class(self, struct_value):
        return forms.MultipleChoiceField if struct_value["multi"] else forms.ChoiceField

    def use_defaults_from_category(self, kwargs, category):
        category_fields = {"label": "name", "help_text": "help_text"}

        for field in category_fields.keys():
            if not kwargs.get(field):
                kwargs[field] = getattr(category, category_fields[field])

        return kwargs

    def get_field_kwargs(self, struct_value):
        kwargs = super().get_field_kwargs(struct_value)
        category = self.get_instance(id=struct_value["category"])
        kwargs = self.use_defaults_from_category(kwargs, category)
        choices = category.options.values_list("id", "value")
        kwargs.update({"choices": choices})
        return kwargs

    def get_widget(self, struct_value):
        if struct_value["multi"]:
            category = self.get_instance(id=struct_value["category"])
            category_size = category.options.count()
            # Pick widget according to number of options to maintain good usability.
            if category_size < 32:
                return forms.CheckboxSelectMultiple
            else:
                return Select2MultipleWidget
        else:
            return forms.RadioSelect

    def prepare_data(self, value, data, serialize):
        if not data:
            return data
        if isinstance(data, str):
            data = [data]
        category = self.get_instance(id=value["category"])
        data = category.options.filter(id__in=data).values_list("value", flat=True)
        return data

    def render(self, value, context):
        # Overwriting field_label and help_text with default for empty values
        category_fields = {"field_label": "name", "help_text": "help_text"}

        for field in category_fields.keys():
            if not value.get(field):
                category = value["category"]
                if isinstance(category, int):
                    category = self.get_instance(id=category)
                value[field] = getattr(category, category_fields[field])
        return super().render(value, context)

    def get_searchable_content(self, value, data):
        return None

    def no_response(self):
        return "-"
