from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.utils.translation import ugettext as _

from wagtail.admin import messages
from wagtail.admin.forms.pages import CopyForm
from wagtail.admin.views.pages import get_valid_next_url_from_request
from wagtail.core import hooks
from wagtail.core.models import Page


def custom_admin_round_copy_view(request, page):
    # Custom view to handle copied Round pages.
    # https://github.com/wagtail/wagtail/blob/124827911463f0cb959edbb9d8d5685578540bd3/wagtail/admin/views/pages.py#L824

    # Parent page defaults to parent of source page
    parent_page = page.get_parent()

    # Check if the user has permission to publish subpages on the parent
    can_publish = parent_page.permissions_for_user(request.user).can_publish_subpage()

    form = CopyForm(request.POST or None, user=request.user, page=page, can_publish=can_publish)

    next_url = get_valid_next_url_from_request(request)

    # Prefill parent_page in case the form is invalid (as prepopulated value for the form field,
    # because ModelChoiceField seems to not fall back to the user given value)
    parent_page = Page.objects.get(id=request.POST['new_parent_page'])

    if form.is_valid():
        # Receive the parent page (this should never be empty)
        if form.cleaned_data['new_parent_page']:
            parent_page = form.cleaned_data['new_parent_page']

        if not page.permissions_for_user(request.user).can_copy_to(parent_page,
                                                                   form.cleaned_data.get('copy_subpages')):
            raise PermissionDenied

        # Re-check if the user has permission to publish subpages on the new parent
        can_publish = parent_page.permissions_for_user(request.user).can_publish_subpage()

        # Copy the page
        new_page = page.copy(
            recursive=form.cleaned_data.get('copy_subpages'),
            to=parent_page,
            update_attrs={
                'title': form.cleaned_data['new_title'],
                'slug': form.cleaned_data['new_slug'],
                'start_date': None,
                'end_date': None,
            },
            keep_live=(can_publish and form.cleaned_data.get('publish_copies')),
            user=request.user,
        )

        messages.info(request, _((
            "Please select the date in the copied page. "
            "Newly copied pages have NONE value for the start and end date"
        )))

        # Give a success message back to the user
        if form.cleaned_data.get('copy_subpages'):
            messages.success(
                request, _("Page '{0}' and {1} subpages copied.").format(
                    page.get_admin_display_title(), new_page.get_descendants().count()
                )
            )
        else:
            messages.success(request, _("Page '{0}' copied.").format(page.get_admin_display_title()))

        for fn in hooks.get_hooks('after_copy_page'):
            result = fn(request, page, new_page)
            if hasattr(result, 'status_code'):
                return result

        # Redirect to explore of parent page
        if next_url:
            return redirect(next_url)
        return redirect('wagtailadmin_explore', parent_page.id)
