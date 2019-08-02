from django import forms
from django.core.exceptions import PermissionDenied
from django.db import models
from django.template.loader import render_to_string

from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.edit_handlers import (
    FieldPanel,
    InlinePanel,
)
from wagtail.admin.forms import WagtailAdminModelForm
from wagtail.core.models import Orderable
from wagtail.search import index

from treebeard.mp_tree import MP_Node


class Option(Orderable):
    value = models.CharField(max_length=255)
    category = ParentalKey('Category', related_name='options')


class Category(ClusterableModel):
    """Used to manage the global select questions used in most of the application form
    Also used in the front end by editors when writing about projects.

    When used in a form: name -> field label and help_text -> help_text
    """
    name = models.CharField(max_length=255)
    help_text = models.CharField(max_length=255, blank=True)

    panels = [
        FieldPanel('name'),
        FieldPanel('help_text'),
        InlinePanel('options', label='Options'),
    ]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Categories'


class MetaCategory(index.Indexed, MP_Node):
    """ Hierarchal "Meta" category """
    name = models.CharField(
        max_length=50, unique=True, help_text='Keep the name short, ideally one word.'
    )

    # node tree specific fields and attributes
    node_order_index = models.IntegerField(blank=True, default=0, editable=False)
    node_child_verbose_name = 'child'

    # important: node_order_by should NOT be changed after first Node created
    node_order_by = ['node_order_index', 'name']

    panels = [
        FieldPanel('parent'),
        FieldPanel('name'),
    ]

    def get_as_listing_header(self):
        depth = self.get_depth()
        rendered = render_to_string(
            'categories/admin/includes/meta_category_list_header.html',
            {
                'depth': depth,
                'depth_minus_1': depth - 1,
                'is_root': self.is_root(),
                'name': self.name,
            }
        )
        return rendered
    get_as_listing_header.short_description = 'Name'
    get_as_listing_header.admin_order_field = 'name'

    def get_parent(self, *args, **kwargs):
        return super().get_parent(*args, **kwargs)
    get_parent.short_description = 'Parent'

    search_fields = [
        index.SearchField('name', partial_match=True),
    ]

    def delete(self):
        if self.is_root():
            raise PermissionDenied('Cannot delete root Category.')
        else:
            super().delete()

    @classmethod
    def get_root_descendants(cls):
        # Meta categories queryset without Root node
        root_node = cls.get_first_root_node()
        if root_node:
            return root_node.get_descendants()
        return cls.objects.none()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Meta Category'
        verbose_name_plural = 'Meta Categories'


class MetaCategoryChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        depth_line = '-' * (obj.get_depth() - 1)
        return "{} {}".format(depth_line, super().label_from_instance(obj))


class MetaCategoryForm(WagtailAdminModelForm):
    parent = MetaCategoryChoiceField(
        required=True,
        queryset=MetaCategory.objects.all(),
        empty_label=None,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs['instance']

        if instance.is_root() or MetaCategory.objects.count() == 0:
            self.fields['parent'].disabled = True
            self.fields['parent'].required = False
            self.fields['parent'].empty_label = 'N/A - Root Category'
            self.fields['parent'].widget = forms.HiddenInput()

            self.fields['name'].label += ' (Root - First category can be named root)'
        elif instance.id:
            self.fields['parent'].initial = instance.get_parent()

    def save(self, commit=True, *args, **kwargs):
        instance = super().save(commit=False, *args, **kwargs)
        parent = self.cleaned_data['parent']

        if not commit:
            return instance

        if instance.id is None:
            if MetaCategory.objects.all().count() == 0:
                MetaCategory.add_root(instance=instance)
            else:
                instance = parent.add_child(instance=instance)
        else:
            instance.save()
            if instance.get_parent() != parent:
                instance.move(parent, pos='sorted-child')
        return instance


MetaCategory.base_form_class = MetaCategoryForm
