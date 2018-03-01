from django.forms import Field, Widget
from django.forms.utils import pretty_name
from django.urls import reverse
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from wagtail.core.models import Page
from wagtail.admin.edit_handlers import BaseFieldPanel, EditHandler, FieldPanel


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


class BaseReadOnlyPanel(EditHandler):
    template = 'wagtailadmin/edit_handlers/single_field_panel.html'
    field_template = 'wagtailadmin/shared/field.html'

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


class ReadOnlyPanel:
    def __init__(self, attr, heading=None, classname=''):
        self.attr = attr
        self.heading = pretty_name(self.attr) if heading is None else heading
        self.classname = classname

    def bind_to_model(self, model):
        kwargs = {
            'attr': self.attr,
            'heading': self.heading,
            'classname': self.classname,
        }
        return type(str(_('ReadOnlyPanel')), (BaseReadOnlyPanel,), kwargs)


class BaseReadOnlyInlinePanel(BaseReadOnlyPanel):
    template = 'wagtailadmin/edit_handlers/multi_field_panel.html'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        values = getattr(self.instance, self.attr).all()
        self.children = [BaseReadOnlyPanel(value, form=self.form) for value in values]


class ReadOnlyInlinePanel:
    def __init__(self, attr, heading=None, classname='', help_text=''):
        self.attr = attr
        self.heading = pretty_name(self.attr) if heading is None else heading
        self.classname = classname
        self.help_text = help_text

    def bind_to_model(self, model):
        kwargs = {
            'attr': self.attr,
            'heading': self.heading,
            'classname': self.classname,
            'help_text': self.help_text
        }
        return type(str(_('ReadOnlyPanel')), (BaseReadOnlyInlinePanel,), kwargs)


class BaseFilteredFieldPanel(BaseFieldPanel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        target_model = self.bound_field.field.queryset.model

        self.bound_field.field.queryset = target_model.objects.filter(**self.filter_query)


class FilteredFieldPanel(FieldPanel):
    def __init__(self, *args, filter_query=dict(), **kwargs):
        self.filter_query = filter_query
        super().__init__(*args, **kwargs)

    def bind_to_model(self, model):
        base = {
            'model': model,
            'field_name': self.field_name,
            'classname': self.classname,
            'filter_query': self.filter_query
        }

        if self.widget:
            base['widget'] = self.widget

        return type(str('_BaseFilteredFieldPanel'), (BaseFilteredFieldPanel,), base)
