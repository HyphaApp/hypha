from django import template

register = template.Library()


@register.filter
def join_with_commas(obj_list: list):
    """
    Takes a list of objects and returns their string representations,
    separated by commas and with 'and' between the penultimate and final items
    For example, for a list of fruit objects:
    [<Fruit: apples>, <Fruit: oranges>, <Fruit: pears>] -> 'apples, oranges and pears'

    Inspired by: https://stackoverflow.com/a/1242107
    """
    if not obj_list:
        return ""
    list_len = len(obj_list)
    if list_len == 1:
        return f"{obj_list[0]}"

    return f"{', '.join(str(obj) for obj in obj_list[: list_len - 1])} and {obj_list[list_len - 1]}"
