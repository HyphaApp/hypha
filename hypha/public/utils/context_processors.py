from django.conf import settings

from hypha.apply.home.models import ApplyHomePage
from hypha.public.home.models import HomePage
from hypha.public.mailchimp.forms import NewsletterForm
from hypha.reset_network.reset_network_home.models import ResetNetworkHomePage


def global_vars(request):
    response = {
        'ORG_LONG_NAME': settings.ORG_LONG_NAME,
        'ORG_SHORT_NAME': settings.ORG_SHORT_NAME,
        'ORG_EMAIL': settings.ORG_EMAIL,
        'MATOMO_URL': settings.MATOMO_URL,
        'MATOMO_SITEID': settings.MATOMO_SITEID,
    }

    if settings.SITE_NAME == 'reset':

        response['APPLY_SITE'] = ApplyHomePage.objects.first().get_site()
        response['PUBLIC_SITE']: ResetNetworkHomePage.objects.first().get_site()

    else:

        response['APPLY_SITE'] = ApplyHomePage.objects.first().get_site()
        response['PUBLIC_SITE']: HomePage.objects.first().get_site()
        response['newsletter_form']: NewsletterForm()
        response['newsletter_enabled']: settings.MAILCHIMP_API_KEY and settings.MAILCHIMP_LIST_ID

    return response
