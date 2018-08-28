from wagtail.core import hooks

from opentech.apply.users.groups import STAFF_GROUP_NAME

from .models import ApplyHomePage


@hooks.register('construct_explorer_page_queryset')
def exclude_fund_pages(parent_page, pages, request):
    # Don't allow editors to access the Apply pages in the explorer unless they know whats up
    if not request.user.is_superuser:
        pages = pages.not_descendant_of(ApplyHomePage.objects.first(), inclusive=True)

    return pages


@hooks.register('construct_main_menu')
def hide_explorer_menu_item_from_frank(request, menu_items):
    if not request.user.is_superuser:
        groups = list(request.user.groups.all())
        # If the user is only in the staff group they should never see the explorer menu item
        if len(groups) == 1 and groups[0].name == STAFF_GROUP_NAME:
            menu_items[:] = [item for item in menu_items if item.name != 'explorer']
