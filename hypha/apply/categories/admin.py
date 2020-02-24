from django.conf.urls import url
from wagtail.contrib.modeladmin.options import ModelAdmin

from .admin_helpers import MetaTermButtonHelper
from .admin_views import AddChildMetaTermViewClass
from .models import Category, MetaTerm


class CategoryAdmin(ModelAdmin):
    menu_label = 'Category Questions'
    menu_icon = 'list-ul'
    model = Category


class MetaTermAdmin(ModelAdmin):
    model = MetaTerm

    menu_icon = 'tag'

    list_per_page = 50
    list_display = ('get_as_listing_header', 'get_parent')
    search_fields = ('name',)

    inspect_view_enabled = True
    inspect_view_fields = ('name', 'get_parent', 'id')

    button_helper_class = MetaTermButtonHelper

    def add_child_view(self, request, instance_pk):
        kwargs = {'model_admin': self, 'parent_pk': instance_pk}
        view_class = AddChildMetaTermViewClass
        return view_class.as_view(**kwargs)(request)

    def get_admin_urls_for_registration(self):
        """Add the new url for add child page to the registered URLs."""
        urls = super().get_admin_urls_for_registration()
        add_child_url = url(
            self.url_helper.get_action_url_pattern('add_child'),
            self.add_child_view,
            name=self.url_helper.get_action_url_name('add_child')
        )
        return urls + (add_child_url, )
