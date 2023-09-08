from django.forms import Field, Widget
from django.template.loader import render_to_string
from django.urls import reverse
from wagtail.admin.panels import FieldPanel, Panel
from wagtail.models import Page


def reverse_edit(obj):
    if isinstance(obj, Page):
        return reverse("wagtailadmin_pages:edit", args=(obj.id,))

    url_name = f"{obj._meta.app_label}_{obj._meta.model_name}_modeladmin_edit"
    return reverse(url_name, args=(obj.id,))


class ReadonlyWidget(Widget):
    template_name = "funds/admin/widgets/read_only.html"

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
            context["widget"]["edit_link"] = edit_link
        return context


class DisplayField(Field):
    widget = ReadonlyWidget


class ReadOnlyPanel(Panel):
    def __init__(self, attr: str, **kwargs):
        super().__init__(**kwargs)
        self.attr = attr

    def clone_kwargs(self):
        """Return a dictionary of keyword arguments that can be used to create
        a clone of this panel definition.
        """
        kwargs = super().clone_kwargs()
        kwargs.update(
            {
                "attr": self.attr,
            }
        )
        return kwargs

    class BoundPanel(Panel.BoundPanel):
        template_name = "wagtailadmin/panels/field_panel.html"

        def render_html(self, parent_context):
            return render_to_string(self.template_name, self.context())

        def context(self):
            try:
                value = getattr(self.instance, self.panel.attr)
            except AttributeError:
                value = self.instance

            if callable(value):
                value = value()

            # Add initial value only when an object is present. Display nothing when a new page is being
            # created. As it is a read-only panel and creates confusion when default values are displayed.
            if self.instance.id:
                self.form.initial[self.panel.attr] = value
            else:
                self.form.initial[self.panel.attr] = "-"

            self.bound_field = DisplayField().get_bound_field(
                self.form, self.panel.attr
            )

            return {
                "self": self,
                "field": self.bound_field,
                "show_label": False,
            }


class FilteredFieldPanel(FieldPanel):
    def __init__(self, *args, filter_query=None, **kwargs):
        if filter_query is None:
            filter_query = {}
        self.filter_query = filter_query
        super().__init__(*args, **kwargs)

    def clone(self):
        return self.__class__(
            field_name=self.field_name,
            widget=self.widget if hasattr(self, "widget") else None,
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
