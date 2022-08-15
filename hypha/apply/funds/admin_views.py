from django.contrib.admin.utils import unquote
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext as _
from wagtail import hooks
from wagtail.admin import messages
from wagtail.admin.forms.pages import CopyForm
from wagtail.admin.views.pages.utils import get_valid_next_url_from_request
from wagtail.contrib.modeladmin.views import CreateView, EditView
from wagtail.models import Page

from hypha.apply.utils.blocks import show_admin_form_error_messages


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


class CopyApplicationFormViewClass(CreateView):
    """View class that can take an additional URL param for parent id."""

    form_pk = None
    form_instance = None

    def __init__(self, model_admin, form_pk):
        self.form_pk = unquote(form_pk)
        object_qs = model_admin.model._default_manager.get_queryset()
        object_qs = object_qs.filter(pk=self.form_pk)
        self.form_instance = get_object_or_404(object_qs)
        super().__init__(model_admin)

    def get_initial(self):
        return {'name': f'[CHANGE] Copy of {self.form_instance.name}', 'form_fields': self.form_instance.form_fields}


class CreateApplicationFormView(CreateView):

    def get_form(self):
        """
        Overriding this method to disable the single file block option from Application Form.
        Set 0 as max_number of single file can be added to make single file block option unavailable or disable.
        """
        form = super(CreateApplicationFormView, self).get_form()
        form.fields['form_fields'].block.meta.block_counts = {'file': {'min_num': 0, 'max_num': 0}}
        return form

    def form_invalid(self, form):
        show_admin_form_error_messages(self.request, form)
        return self.render_to_response(self.get_context_data(form=form))


class EditApplicationFormView(EditView):

    def get_form(self):
        """
        Overriding this method to disable the single file block option from Application Form.
        Calculating the number of Single file blocks that exist in the instance already.
        And set that count as max_number of single file block can be added to make single file option disable.
        """
        form = super(EditApplicationFormView, self).get_form()
        single_file_count = sum(1 for block in self.get_instance().form_fields.raw_data if block['type'] == 'file')
        form.fields['form_fields'].block.meta.block_counts = {'file': {'min_num': 0, 'max_num': single_file_count}}
        return form

    def form_invalid(self, form):
        show_admin_form_error_messages(self.request, form)
        return self.render_to_response(self.get_context_data(form=form))
