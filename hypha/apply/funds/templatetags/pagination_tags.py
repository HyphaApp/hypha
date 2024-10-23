from django import template
from django.http import HttpRequest

register = template.Library()


@register.filter
def get_pagination_url(request: HttpRequest, page: int):
    params = request.GET.copy()
    params["page"] = page
    return f"?{params.urlencode()}"
