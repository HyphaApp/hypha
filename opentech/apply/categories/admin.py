from django.conf.urls import url
from wagtail.contrib.modeladmin.options import ModelAdmin

from .admin_helpers import MetaCategoryButtonHelper
from .admin_views import AddChildMetaCategoryViewClass
from .models import Category, MetaCategory


class CategoryAdmin(ModelAdmin):
    menu_label = 'Category Questions'
    menu_icon = 'list-ul'
    model = Category


class MetaCategoryAdmin(ModelAdmin):
    model = MetaCategory

    menu_icon = 'tag'

    list_per_page = 50
    list_display = ('get_as_listing_header', 'get_parent')
    search_fields = ('name',)

    inspect_view_enabled = True
    inspect_view_fields = ('name', 'get_parent', 'id')

    button_helper_class = MetaCategoryButtonHelper

    def add_child_view(self, request, instance_pk):
        kwargs = {'model_admin': self, 'parent_pk': instance_pk}
        view_class = AddChildMetaCategoryViewClass
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
