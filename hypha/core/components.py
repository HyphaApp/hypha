import uuid

from django_web_components import component


@component.register("dropdown-item")
class DropdownMenu(component.Component):
    template_name = "components/dropdown-menu.html"

    def get_context_data(self, **kwargs) -> dict:
        return {"id": str(uuid.uuid4())}


@component.register("scroll-to-top")
class ScrollToTop(component.Component):
    template_name = "components/scroll-to-top.html"
