from wagtail.core import hooks
from wagtail.contrib.modeladmin.options import modeladmin_register

from .admin import ApplyAdminGroup
from .models import Round


modeladmin_register(ApplyAdminGroup)


@hooks.register('before_create_page')
def before_create_page(request, parent_page, page_class):
    if page_class == Round:
        page_class.parent_page = parent_page
    return page_class
