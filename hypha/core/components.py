from django_web_components import component


@component.register("admin_bar")
class AdminBar(component.Component):
    template_name = "components/admin_bar.html"
