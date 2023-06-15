import uuid

from django_web_components import component


@component.register("admin_bar")
class AdminBar(component.Component):
    template_name = "components/admin_bar.html"


@component.register("dropdown-item")
class DropdownMenu(component.Component):
    template_name = "components/dropdown-menu.html"

    def get_context_data(self, **kwargs) -> dict:
        return {
            'id': str(uuid.uuid4())
        }
