from django.contrib.auth.models import Permission

from wagtail.core import hooks
from wagtail.contrib.modeladmin.options import modeladmin_register

from .admin import ApplyAdminGroup
from .admin_views import custom_admin_round_copy_view
from .models import RoundBase


modeladmin_register(ApplyAdminGroup)


@hooks.register('before_create_page')
def before_create_page(request, parent_page, page_class):
    if issubclass(page_class, RoundBase) and request.POST:
        if not hasattr(page_class, 'parent_page'):
            page_class.parent_page = {}
        page_class.parent_page.setdefault(page_class, {})[request.POST['title']] = parent_page
    return page_class


@hooks.register('before_copy_page')
def before_copy_round_page(request, page):
    if isinstance(page.specific, RoundBase) and request.method == 'POST':
        # Custom view to clear start_date and end_date from the copy being created.
        return custom_admin_round_copy_view(request, page)


@hooks.register('register_permissions')
def register_permissions():
    return Permission.objects.filter(
        content_type__app_label='funds',
        codename__in=['add_applicationsubmission', 'change_applicationsubmission', 'delete_applicationsubmission']
    )
