from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register

from .admin_view import CreateInvestmentView, EditInvestmentView
from .models import Investment


class InvestmentAdmin(ModelAdmin):
    model = Investment
    create_view_class = CreateInvestmentView
    edit_view_class = EditInvestmentView
    form_fields_exclude = ("application",)
    menu_label = "Investments"
    menu_icon = "placeholder"
    menu_order = 290
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ("partner", "name", "amount_committed", "year")
    list_filter = ("partner__title", "year", "amount_committed")
    search_fields = ("name", "year")


modeladmin_register(InvestmentAdmin)
