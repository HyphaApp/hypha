from django.contrib.admin.utils import quote

from wagtail.contrib.modeladmin.helpers import ButtonHelper


class MetaTermButtonHelper(ButtonHelper):
    def delete_button(self, pk, *args, **kwargs):
        """Ensure that the delete button is not shown for root meta term."""
        instance = self.model.objects.get(pk=pk)
        if instance.is_root():
            return
        return super().delete_button(pk, *args, **kwargs)

    def prepare_classnames(self, start=None, add=None, exclude=None):
        """Parse classname sets into final css classess list."""
        classnames = start or []
        classnames.extend(add or [])
        return self.finalise_classname(classnames, exclude or [])

    def add_child_button(self, pk, child_verbose_name, **kwargs):
        """Build a add child button, to easily add a child under meta term."""
        instance = self.model.objects.get(pk=pk)
        if instance.is_archived or instance.get_parent() and instance.get_parent().is_archived:
            return

        classnames = self.prepare_classnames(
            start=self.edit_button_classnames + ['icon', 'icon-plus'],
            add=kwargs.get('classnames_add'),
            exclude=kwargs.get('classnames_exclude')
        )
        return {
            'classname': classnames,
            'label': 'Add %s %s' % (
                child_verbose_name, self.verbose_name),
            'title': 'Add %s %s under this one' % (
                child_verbose_name, self.verbose_name),
            'url': self.url_helper.get_action_url('add_child', quote(pk)),
        }

    def get_buttons_for_obj(self, obj, exclude=None, *args, **kwargs):
        """Override the getting of buttons, prepending create child button."""
        buttons = super().get_buttons_for_obj(obj, *args, **kwargs)

        add_child_button = self.add_child_button(
            pk=getattr(obj, self.opts.pk.attname),
            child_verbose_name=getattr(obj, 'node_child_verbose_name'),
            **kwargs
        )
        buttons.append(add_child_button)

        return buttons
