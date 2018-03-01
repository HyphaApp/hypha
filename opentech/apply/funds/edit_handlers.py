from django.forms import Field, Widget
from django.forms.utils import pretty_name
from django.urls import reverse
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from wagtail.core.models import Page
from wagtail.admin.edit_handlers import EditHandler, FieldPanel


def reverse_edit(obj):
    if isinstance(obj, Page):
        return reverse('wagtailadmin_pages:edit', args=(obj.id,))

    url_name = f'{obj._meta.app_label}_{obj._meta.model_name}_modeladmin_edit'
    return reverse(url_name, args=(obj.id,))


class ReadonlyWidget(Widget):
    template_name = 'funds/admin/widgets/read_only.html'

    def format_value(self, value):
        self.value = value
        return super().format_value(value)

    def get_context(self, *args, **kwargs):
        context = super().get_context(*args, **kwargs)
        try:
            # Hard coded accessing the related model (form) BEWARE if reusing
            edit_link = reverse_edit(self.value.form)
        except AttributeError:
            pass
        else:
            context['widget']['edit_link'] = edit_link
        return context


class DisplayField(Field):
    widget = ReadonlyWidget


class ReadOnlyPanel(EditHandler):
    template = 'wagtailadmin/edit_handlers/single_field_panel.html'
    field_template = 'wagtailadmin/shared/field.html'

    def __init__(self, attr, **kwargs):
        self.attr = attr
        super().__init__(**kwargs)
        self.heading = pretty_name(self.attr) if self.heading is None else self.heading

    def context(self):
        try:
            value = getattr(self.instance, self.attr)
        except AttributeError:
            self.attr = '__'.join([self.instance._meta.model_name, str(self.instance.id)])
            value = self.instance

        if callable(value):
            value = value()

        self.form.initial[self.attr] = value
        self.bound_field = DisplayField().get_bound_field(self.form, self.attr)
        return {
            'self': self,
            'field': self.bound_field,
            'show_label': False,
        }

    def render_as_object(self):
        return render_to_string(self.template, self.context())

    def render_as_field(self):
        return render_to_string(self.field_template, self.context())


class ReadOnlyInlinePanel(ReadOnlyPanel):
    template = 'wagtailadmin/edit_handlers/multi_field_panel.html'

    def on_model_bound(self, model):
        values = getattr(self.instance, self.attr).all()
        self.children = [ReadOnlyPanel(value, form=self.form) for value in values]


class FilteredFieldPanel(FieldPanel):
    def __init__(self, *args, filter_query=dict(), **kwargs):
        self.filter_query = filter_query
        super().__init__(*args, **kwargs)

    def clone(self):
        return self.__class__(
            field_name=self.field_name,
            widget=self.widget if hasattr(self, 'widget') else None,
            heading=self.heading,
            classname=self.classname,
            help_text=self.help_text,
            filter_query=self.filter_query,
        )

    def on_instance_bound(self):
        super().on_instance_bound()
        target_model = self.bound_field.field.queryset.model
        self.bound_field.field.queryset = target_model.objects.filter(**self.filter_query)
