from wagtail.contrib.modeladmin.views import CreateView, EditView

from hypha.apply.utils.blocks import show_admin_form_error_messages


class CreateProjectApprovalFormView(CreateView):
    def form_invalid(self, form):
        show_admin_form_error_messages(self.request, form)
        return self.render_to_response(self.get_context_data(form=form))


class EditProjectApprovalFormView(EditView):
    def form_invalid(self, form):
        show_admin_form_error_messages(self.request, form)
        return self.render_to_response(self.get_context_data(form=form))


class CreateProjectSOWFormView(CreateProjectApprovalFormView):
    pass


class EditProjectSOWFormView(EditProjectApprovalFormView):
    pass


class CreateProjectReportFormView(CreateProjectApprovalFormView):
    pass


class EditProjectReportFormView(EditProjectApprovalFormView):
    pass
