from django.forms.utils import pretty_name
from django.urls import reverse
from django.utils.html import format_html, mark_safe
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailcore.models import Page
from wagtail.wagtailadmin.edit_handlers import EditHandler


class BaseReadOnlyPanel(EditHandler):
    def render(self):
        value = getattr(self.instance, self.attr)
        if callable(value):
            value = value()
        return format_html('<div style="padding-top: 1.2em;">{}</div>', value)

    def render_as_object(self):
        return format_html(
            '<fieldset><legend>{}</legend>'
            '<ul class="fields"><li><div class="field">{}</div></li></ul>'
            '</fieldset>',
            self.heading, self.render())

    def render_as_field(self):
        return format_html(
            '<div class="field">'
            '<label>{}{}</label>'
            '<div class="field-content">{}</div>'
            '</div>',
            self.heading, _(':'), self.render())


class ReadOnlyPanel:
    def __init__(self, attr, heading=None, classname=''):
        self.attr = attr
        self.heading = pretty_name(self.attr) if heading is None else heading
        self.classname = classname

    def bind_to_model(self, model):
        return type(str(_('ReadOnlyPanel')), (BaseReadOnlyPanel,),
                    {'attr': self.attr, 'heading': self.heading,
                     'classname': self.classname})


def reverse_edit(obj):
    if isinstance(obj, Page):
        return reverse('wagtailadmin_pages:edit', args=(obj.id,))

    url_name = f'{obj._meta.app_label}_{obj._meta.model_name}_modeladmin_edit'
    return reverse(url_name, args=(obj.id,))


class BaseReadOnlyInlinePanel(BaseReadOnlyPanel):
    def render(self):
        values = getattr(self.instance, self.attr).all()
        return mark_safe(
            ''.join(
                '<div style="padding-top: 1.2em;">'
                f'{value}<br><a class="button button-small" href="{reverse_edit(value.form)}">Edit</a></div>'
                for value in values
            )
        )


class ReadOnlyInlinePanel:
    def __init__(self, attr, heading=None, classname=''):
        self.attr = attr
        self.heading = pretty_name(self.attr) if heading is None else heading
        self.classname = classname

    def bind_to_model(self, model):
        return type(str(_('ReadOnlyPanel')), (BaseReadOnlyInlinePanel,),
                    {'attr': self.attr, 'heading': self.heading,
                     'classname': self.classname})
