from wagtail.contrib.modeladmin.views import CreateView, EditView

from hypha.apply.utils.blocks import show_admin_form_error_messages


class CreateProjectApprovalFormView(CreateView):

    def get_form(self):
        """
        Overriding this method to disable the single file block option from Project Approval Form.
        Set 0 as max_number of single file can be added to make single file block option unavailable or disable.
        """
        form = super(CreateProjectApprovalFormView, self).get_form()
        form.fields['form_fields'].block.meta.block_counts = {'file': {'min_num': 0, 'max_num': 0}}
        return form

    def form_invalid(self, form):
        show_admin_form_error_messages(self.request, form)
        return self.render_to_response(self.get_context_data(form=form))


class EditProjectApprovalFormView(EditView):

    def get_form(self):
        """
        Overriding this method to disable the single file block option from Project Approval Form.
        Calculating the number of Single file blocks that exist in the instance already.
        And set that count as max_number of single file block can be added to make single file option disable.
        """
        form = super(EditProjectApprovalFormView, self).get_form()
        single_file_count = sum(1 for block in self.get_instance().form_fields.raw_data if block['type'] == 'file')
        form.fields['form_fields'].block.meta.block_counts = {'file': {'min_num': 0, 'max_num': single_file_count}}
        return form

    def form_invalid(self, form):
        show_admin_form_error_messages(self.request, form)
        return self.render_to_response(self.get_context_data(form=form))
