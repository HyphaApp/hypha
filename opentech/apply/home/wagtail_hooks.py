from wagtail.core import hooks

from .models import ApplyHomePage


@hooks.register('construct_explorer_page_queryset')
def exclude_fund_pages(parent_page, pages, request):
    # Don't allow editors to access the Apply pages in the explorer unless they know whats up
    if not request.user.is_superuser:
        pages = pages.not_ancestor_of(ApplyHomePage.objects.first(), inclusive=True)

    return pages
