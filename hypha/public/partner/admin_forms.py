from django import forms

from wagtail.admin.forms import WagtailAdminModelForm

from .settings import InvestmentCategorySettings


class InvestmentAdminForm(WagtailAdminModelForm):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        ics = InvestmentCategorySettings.for_request(self.request)
        categories = ics.categories.all()
        for category in categories:
            field_name = category.name.lower().replace(' ', '_')
            self.fields[field_name] = forms.ModelChoiceField(
                required=False,
                queryset=category.options.all(),
            )
