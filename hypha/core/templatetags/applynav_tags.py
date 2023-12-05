import copy

from django import template

from ..navigation import nav_items

register = template.Library()


@register.simple_tag
def apply_nav_items(user):
    temp_nav = copy.deepcopy(nav_items)
    item_count = 0
    for item in nav_items:
        item_count = +1
        removed = False
        if isinstance(item["user_roles"], list):
            if not bool(
                set(user.groups.all().values_list("name", flat=True))
                & set(item["user_roles"])
            ):
                temp_nav.remove(item)
                removed = True
                item_count = -1
        if not removed and "categories" in item.keys():
            for item_category in item["categories"]:
                if isinstance(item_category["user_roles"], list):
                    if not bool(
                        set(user.groups.all().values_list("name", flat=True))
                        & set(item_category["user_roles"])
                    ):
                        temp_nav[item_count]["categories"].remove(item_category)
    return temp_nav
