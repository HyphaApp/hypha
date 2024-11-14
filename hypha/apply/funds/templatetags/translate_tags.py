from django import template
from django.conf import settings

register = template.Library()


@register.filter
def can_translate_submission(user) -> bool:
    """Verify that system settings & user role allows for submission translations.

    Args:
        user: the user to check the role of.

    Returns:
        bool: true if submission can be translated, false if not.

    """
    return bool(settings.APPLICATION_TRANSLATIONS_ENABLED and user.is_org_faculty)
