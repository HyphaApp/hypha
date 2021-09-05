from django import template

from hypha.apply.projects.models import PaymentRequest

register = template.Library()


# Get the verbose name of a model instance
@register.filter
def model_verbose_name(instance):
    title = instance._meta.verbose_name.title()
    # to show payment request name in text
    if isinstance(instance, PaymentRequest):
        return str(title + ': ' + str(instance.project) + str(instance.id))
    return title
