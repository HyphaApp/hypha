from django import template

from hypha.apply.categories.models import Option

register = template.Library()


@register.filter
def get_category_label(label_id: int) -> str:
    """Get the category string label of a selected category

    Args:
        label_id:
            The ID of the label to get the string representation of

    Returns:
        A representation of the label
    """
    return str(Option.objects.get(id=label_id))
