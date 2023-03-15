from django.conf import settings


def global_vars(request):
    return {
        'SENTRY_TRACES_SAMPLE_RATE': settings.SENTRY_TRACES_SAMPLE_RATE,
        'SENTRY_ENVIRONMENT': settings.SENTRY_ENVIRONMENT,
        'SENTRY_DENY_URLS': settings.SENTRY_DENY_URLS,
        'SENTRY_DEBUG': settings.SENTRY_DEBUG,
        'SENTRY_PUBLIC_KEY': settings.SENTRY_PUBLIC_KEY,
    }
