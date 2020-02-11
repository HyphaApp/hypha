from django.contrib.admin.utils import unquote
from django.shortcuts import get_object_or_404

from wagtail.contrib.modeladmin.views import CreateView


class AddChildMetaTermViewClass(CreateView):
    """View class that can take an additional URL param for parent id."""

    parent_pk = None
    parent_instance = None

    def __init__(self, model_admin, parent_pk):
        self.parent_pk = unquote(parent_pk)
        object_qs = model_admin.model._default_manager.get_queryset()
        object_qs = object_qs.filter(pk=self.parent_pk)
        self.parent_instance = get_object_or_404(object_qs)
        super().__init__(model_admin)

    def get_page_title(self):
        """Generate a title that explains you are adding a child."""
        title = super().get_page_title()
        return title + ' %s %s for %s' % (
            self.model.node_child_verbose_name,
            self.opts.verbose_name,
            self.parent_instance
        )

    def get_initial(self):
        """Set the selected parent field to the parent_pk."""
        return {'parent': self.parent_pk}
