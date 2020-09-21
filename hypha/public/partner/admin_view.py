from wagtail.admin.edit_handlers import FieldPanel
from wagtail.contrib.modeladmin.views import CreateView, EditView

from .models import InvestmentCategorySettings


class CreateInvestmentView(CreateView):
    def get_form_kwargs(self):
        kwargs = super(CreateInvestmentView, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self):
        context = super(CreateInvestmentView, self).get_context_data()
        ics = InvestmentCategorySettings.for_request(self.request)
        categories = ics.categories.all()
        for category in categories:
            field_name = category.name.lower().replace(' ', '_')
            field_panel = FieldPanel(field_name).bind_to(
                model=self.model,
                instance=context['edit_handler'].instance,
                request=context['edit_handler'].request,
                form=context['form']
            )
            context['edit_handler'].children.append(field_panel)
        return context


class EditInvestmentView(EditView):
    def get_form_kwargs(self):
        kwargs = super(EditInvestmentView, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self):
        context = super(EditInvestmentView, self).get_context_data()
        ics = InvestmentCategorySettings.for_request(self.request)
        categories = ics.categories.all()
        for category in categories:
            field_name = category.name.lower().replace(' ', '_')
            field_panel = FieldPanel(field_name).bind_to(
                model=self.model,
                instance=context['edit_handler'].instance,
                request=context['edit_handler'].request,
                form=context['form']
            )
            context['edit_handler'].children.append(field_panel)
        return context
