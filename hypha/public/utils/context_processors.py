from django.conf import settings

from hypha.apply.home.models import ApplyHomePage
from hypha.public.home.models import HomePage
from hypha.public.mailchimp.forms import NewsletterForm


def global_vars(request):
    return {
        'APPLY_SITE': ApplyHomePage.objects.first().get_site(),
        'PUBLIC_SITE': HomePage.objects.first().get_site(),
        'newsletter_form': NewsletterForm(),
        'newsletter_enabled': settings.MAILCHIMP_API_KEY and settings.MAILCHIMP_LIST_ID,
        'ORG_LONG_NAME': settings.ORG_LONG_NAME,
        'ORG_SHORT_NAME': settings.ORG_SHORT_NAME,
        'ORG_TECH_EMAIL': settings.ORG_TECH_EMAIL,
        'ORG_STAFF_EMAIL': settings.ORG_STAFF_EMAIL,
        'MATOMO_URL': settings.MATOMO_URL,
        'MATOMO_SITEID': settings.MATOMO_SITEID,
        'CURRENCY_SYMBOL': settings.CURRENCY_SYMBOL,
    }
