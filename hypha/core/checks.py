from django.conf import settings
from django.core.checks import Warning, register

W001 = "hypha.core.W001"
W002 = "hypha.core.W002"
W003 = "hypha.core.W003"


@register()
def primary_host_deprecated(app_configs, **kwargs):
    """PRIMARY_HOST is deprecated in favour of WAGTAILADMIN_BASE_URL."""
    primary_host = getattr(settings, "PRIMARY_HOST", None)
    if not primary_host:
        return []

    warnings = [
        Warning(
            "The PRIMARY_HOST setting is deprecated.",
            hint=(
                "Set WAGTAILADMIN_BASE_URL to the full base URL of the site, "
                "including the scheme, and remove PRIMARY_HOST."
            ),
            id=W001,
        )
    ]

    if "://" in primary_host:
        warnings.append(
            Warning(
                f"PRIMARY_HOST should be a bare hostname, not '{primary_host}'.",
                hint=(
                    "'https://' is prepended to PRIMARY_HOST, so a value that "
                    "already includes a scheme produces a broken base URL. Set "
                    "WAGTAILADMIN_BASE_URL instead."
                ),
                id=W002,
            )
        )

    return warnings


@register()
def base_url_not_set(app_configs, **kwargs):
    """WAGTAILADMIN_BASE_URL is needed to build links in notifications."""
    if getattr(settings, "WAGTAILADMIN_BASE_URL", None):
        return []

    return [
        Warning(
            "The WAGTAILADMIN_BASE_URL setting is not set.",
            hint=(
                "Links in emails and Slack messages fall back to the default "
                "Wagtail site, which does not know if the site is served over "
                "HTTPS. Set WAGTAILADMIN_BASE_URL to the full base URL of the "
                "site, including the scheme, e.g. 'https://apply.example.org'."
            ),
            id=W003,
        )
    ]
