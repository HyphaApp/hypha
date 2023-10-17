from django.conf import settings

from hypha.apply.home.models import ApplyHomePage


def global_vars(request):
    return {
        "APPLY_SITE": ApplyHomePage.objects.first().get_site(),
        "ORG_LONG_NAME": settings.ORG_LONG_NAME,
        "ORG_SHORT_NAME": settings.ORG_SHORT_NAME,
        "ORG_EMAIL": settings.ORG_EMAIL,
        "ORG_GUIDE_URL": settings.ORG_GUIDE_URL,
        "ORG_URL": settings.ORG_URL,
        "GOOGLE_OAUTH2": settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY,
        "ENABLE_REGISTRATION_WITHOUT_APPLICATION": settings.ENABLE_REGISTRATION_WITHOUT_APPLICATION,
        "ENABLE_GOOGLE_TRANSLATE": settings.ENABLE_GOOGLE_TRANSLATE,
        "SENTRY_TRACES_SAMPLE_RATE": settings.SENTRY_TRACES_SAMPLE_RATE,
        "SENTRY_ENVIRONMENT": settings.SENTRY_ENVIRONMENT,
        "SENTRY_DENY_URLS": settings.SENTRY_DENY_URLS,
        "SENTRY_DEBUG": settings.SENTRY_DEBUG,
        "SENTRY_PUBLIC_KEY": settings.SENTRY_PUBLIC_KEY,
    }
