from wagtail.contrib.modeladmin.views import CreateView, EditView

from hypha.apply.utils.blocks import show_admin_form_error_messages


class CreateProjectFormView(CreateView):
    def form_invalid(self, form):
        show_admin_form_error_messages(self.request, form)
        return self.render_to_response(self.get_context_data(form=form))


class EditProjectFormView(EditView):
    def form_invalid(self, form):
        show_admin_form_error_messages(self.request, form)
        return self.render_to_response(self.get_context_data(form=form))


class CreateProjectSOWFormView(CreateProjectFormView):
    pass


class EditProjectSOWFormView(EditProjectFormView):
    pass


class CreateProjectReportFormView(CreateProjectFormView):
    pass


class EditProjectReportFormView(EditProjectFormView):
    pass
