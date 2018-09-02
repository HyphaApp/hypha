from wagtail.core import hooks
from wagtail.contrib.modeladmin.options import modeladmin_register

from .admin import ApplyAdminGroup
from .models import RoundBase


modeladmin_register(ApplyAdminGroup)


@hooks.register('before_create_page')
def before_create_page(request, parent_page, page_class):
    if issubclass(page_class, RoundBase) and request.POST:
        if not hasattr(page_class, 'parent_page'):
            page_class.parent_page = {}
        page_class.parent_page.setdefault(page_class, {})[request.POST['title']] = parent_page
    return page_class
