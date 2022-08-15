from django.forms import Field, Widget
from django.forms.utils import pretty_name
from django.template.loader import render_to_string
from django.urls import reverse
from wagtail.admin.panels import FieldPanel, Panel
from wagtail.models import Page


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


class ReadOnlyPanel(Panel):
    def __init__(self, attr, **kwargs):
        self.attr = attr
        super().__init__(**kwargs)
        self.heading = pretty_name(self.attr) if not self.heading else self.heading

    def clone(self):
        return self.__class__(
            attr=self.attr,
            heading=self.heading,
            classname=self.classname,
            help_text=self.help_text,
        )

    class BoundPanel(Panel.BoundPanel):
        field_template_name = 'wagtailadmin/shared/field.html'
        template_name = 'wagtailadmin/panels/single_field_panel.html'

        def render_as_object(self):
            return render_to_string(self.template_name, self.context())

        def render_as_field(self):
            return render_to_string(self.field_template_name, self.context())

        def context(self):
            try:
                value = getattr(self.instance, self.attr)
            except AttributeError:
                self.attr = '__'.join(
                    [self.instance._meta.model_name, str(self.instance.id)]
                )
                value = self.instance

            if callable(value):
                value = value()

            # Add initial value only when an object is present. Display nothing when a new page is being
            # created. As it is a read-only panel and creates confusion when default values are displayed.
            if self.instance.id:
                self.form.initial[self.attr] = value
            else:
                self.form.initial[self.attr] = '-'
            self.bound_field = DisplayField().get_bound_field(self.form, self.attr)
            return {
                'self': self,
                'field': self.bound_field,
                'show_label': False,
            }


class ReadOnlyInlinePanel(ReadOnlyPanel):
    template_name = 'wagtailadmin/panels/multi_field_panel.html'

    def get_child_edit_handler(self):
        child_edit_handler = ReadOnlyPanel(self.attr)
        model = getattr(self.instance, self.attr)
        return child_edit_handler.bind_to(model=model)

    class BoundPanel(ReadOnlyPanel.BoundPanel):
        def on_instance_bound(self):
            values = getattr(self.instance, self.attr).all()
            child_panel = self.get_child_edit_handler()
            self.children = [
                child_panel.bind_to(
                    instance=value, form=self.form, request=self.request
                )
                for value in values
            ]


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

    class BoundPanel(FieldPanel.BoundPanel):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            target_model = self.bound_field.field.queryset.model
            self.bound_field.field.queryset = target_model.objects.filter(
                **self.panel.filter_query
            )
