from django.conf import settings

from hypha.apply.home.models import ApplyHomePage
from hypha.public.home.models import HomePage


def global_vars(request):
    return {
        'APPLY_SITE': ApplyHomePage.objects.first().get_site(),
        'PUBLIC_SITE': HomePage.objects.first().get_site(),
        'ORG_LONG_NAME': settings.ORG_LONG_NAME,
        'ORG_SHORT_NAME': settings.ORG_SHORT_NAME,
        'ORG_EMAIL': settings.ORG_EMAIL,
        'ORG_GUIDE_URL': settings.ORG_GUIDE_URL,
        'ORG_URL': settings.ORG_URL,
        'MATOMO_URL': settings.MATOMO_URL,
        'MATOMO_SITEID': settings.MATOMO_SITEID,
        'CURRENCY_SYMBOL': settings.CURRENCY_SYMBOL,
        'GOOGLE_OAUTH2': settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY,
    }
