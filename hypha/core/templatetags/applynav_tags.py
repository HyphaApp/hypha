import copy

from django import template
from django.core.exceptions import PermissionDenied

from hypha.apply.users import decorators

from ..navigation import nav_items

register = template.Library()


def has_permission(user, method):
    try:
        if getattr(decorators, method)(user):
            return True
        return False
    except PermissionDenied:
        return False
    except Exception:
        # just to handle unknown exceptions
        return False


@register.simple_tag
def apply_nav_items(user):
    temp_nav = copy.deepcopy(nav_items)
    item_count = 0
    for item in nav_items:
        item_count = +1
        removed = False
        if not has_permission(user, item["permission_method"]):
            temp_nav.remove(item)
            removed = True
            item_count = -1
        if not removed and "sub_items" in item.keys():
            for sub_item in item["sub_items"]:
                if not has_permission(user, sub_item["permission_method"]):
                    temp_nav[item_count]["sub_items"].remove(sub_item)
    return temp_nav
