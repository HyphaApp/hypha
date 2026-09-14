from django.conf import settings
from django.contrib.auth.models import Permission
from django.utils.safestring import mark_safe
from wagtail import hooks
from wagtail_modeladmin.options import modeladmin_register

from .admin import ApplyAdminGroup
from .admin_views import custom_admin_round_copy_view
from .models import RoundBase

modeladmin_register(ApplyAdminGroup)


@hooks.register("before_create_page")
def before_create_page(request, parent_page, page_class):
    if issubclass(page_class, RoundBase) and request.POST:
        if not hasattr(page_class, "parent_page"):
            page_class.parent_page = {}
        page_class.parent_page.setdefault(page_class, {})[request.POST["title"]] = (
            parent_page
        )
    return page_class


@hooks.register("before_copy_page")
def before_copy_round_page(request, page):
    if isinstance(page.specific, RoundBase) and request.method == "POST":
        # Custom view to clear start_date and end_date from the copy being created.
        return custom_admin_round_copy_view(request, page)


@hooks.register("register_permissions")
def register_permissions():
    return Permission.objects.filter(
        content_type__app_label="funds",
        codename__in=[
            "add_applicationsubmission",
            "change_applicationsubmission",
            "delete_applicationsubmission",
        ],
    )


@hooks.register("construct_main_menu")
def hide_forms_menu_item(request, menu_items):
    """Hides the "Forms" menu item from the main menu.

    The "Forms" menu item is added by wagtail.contrib.forms.
    """
    menu_items[:] = [item for item in menu_items if item.name != "forms"]
    return menu_items


@hooks.register("insert_global_admin_css")
def hide_pii_field_checkbox():
    """Hide the "Personal information" checkbox on form field blocks.

    `PII_FIELD_MARKING_ENABLED` decides whether form authors are offered the
    checkbox, nothing more. It is not an access control: redaction is never
    gated on it, so a field that carries the mark already keeps being redacted
    whatever the setting is. That is deliberate, see
    `docs/setup/administrators/pii-fields.md`, since turning the setting off
    should never expose an answer someone marked as personal.

    The rule is global admin CSS, so it hides any `is_pii` field in the Wagtail
    admin. Only the application form field blocks have one.
    """
    if settings.PII_FIELD_MARKING_ENABLED:
        return ""
    return mark_safe('<style>[data-contentpath="is_pii"]{display:none}</style>')
