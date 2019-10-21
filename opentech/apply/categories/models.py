from django import forms
from django.core.exceptions import PermissionDenied
from django.db import models
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.edit_handlers import (
    FieldPanel,
    InlinePanel,
    MultiFieldPanel,
)
from wagtail.admin.forms import WagtailAdminModelForm
from wagtail.core.fields import RichTextField
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


class MetaTerm(index.Indexed, MP_Node):
    """ Hierarchal "Meta" terms """
    name = models.CharField(
        max_length=50, unique=True, help_text='Keep the name short, ideally one word.'
    )
    is_archived = models.BooleanField(
        default=False, verbose_name=_("Archived"),
        help_text='Archived terms can be viewed but not set on content.'
    )
    filter_on_dashboard = models.BooleanField(
        default=True, help_text='Make available to filter on dashboard'
    )
    available_to_applicants = models.BooleanField(
        default=False, help_text='Make available to applicants'
    )
    help_text = RichTextField(features=[
        'h2', 'h3', 'bold', 'italic', 'link', 'hr', 'ol', 'ul'], blank=True)

    # node tree specific fields and attributes
    node_order_index = models.IntegerField(blank=True, default=0, editable=False)
    node_child_verbose_name = 'child'

    # important: node_order_by should NOT be changed after first Node created
    node_order_by = ['node_order_index', 'name']

    panels = [
        FieldPanel('name'),
        FieldPanel('parent'),
        MultiFieldPanel(
            [
                FieldPanel('is_archived'),
                FieldPanel('filter_on_dashboard'),
                FieldPanel('available_to_applicants'),
                FieldPanel('help_text'),
            ],
            heading="Options",
        ),
    ]

    def get_as_listing_header(self):
        depth = self.get_depth()
        rendered = render_to_string(
            'categories/admin/includes/meta_term_list_header.html',
            {
                'depth': depth,
                'depth_minus_1': depth - 1,
                'is_root': self.is_root(),
                'name': self.name,
                'is_archived': self.is_archived,
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
            raise PermissionDenied('Cannot delete root term.')
        else:
            super().delete()

    @classmethod
    def get_root_descendants(cls):
        # Meta terms queryset without Root node
        root_node = cls.get_first_root_node()
        if root_node:
            return root_node.get_descendants()
        return cls.objects.none()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Meta Term'
        verbose_name_plural = 'Meta Terms'


class MetaTermChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        depth_line = '-' * (obj.get_depth() - 1)
        return "{} {}".format(depth_line, super().label_from_instance(obj))


class MetaTermForm(WagtailAdminModelForm):
    parent = MetaTermChoiceField(
        required=True,
        queryset=MetaTerm.objects.all(),
        empty_label=None,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs['instance']

        if instance.is_root() or MetaTerm.objects.count() == 0:
            self.fields['parent'].disabled = True
            self.fields['parent'].required = False
            self.fields['parent'].empty_label = 'N/A - Root Term'
            self.fields['parent'].widget = forms.HiddenInput()

            self.fields['name'].label += ' (Root - First term can be named root)'
        elif instance.id:
            self.fields['parent'].initial = instance.get_parent()

    def clean_parent(self):
        parent = self.cleaned_data['parent']

        if parent and parent.is_archived:
            raise forms.ValidationError('The parent is archived therefore can not add child under it.')

        return parent

    def save(self, commit=True, *args, **kwargs):
        instance = super().save(commit=False, *args, **kwargs)
        parent = self.cleaned_data['parent']

        if not commit:
            return instance

        if instance.id is None:
            if MetaTerm.objects.all().count() == 0:
                MetaTerm.add_root(instance=instance)
            else:
                instance = parent.add_child(instance=instance)
        else:
            instance.save()
            if instance.get_parent() != parent:
                instance.move(parent, pos='sorted-child')
        return instance


MetaTerm.base_form_class = MetaTermForm
