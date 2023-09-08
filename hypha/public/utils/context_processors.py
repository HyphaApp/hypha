from django.conf import settings

from hypha.public.home.models import HomePage
from hypha.public.mailchimp.forms import NewsletterForm


def global_vars(request):
    return {
        "PUBLIC_SITE": HomePage.objects.first().get_site(),
        "newsletter_form": NewsletterForm(),
        "newsletter_enabled": settings.MAILCHIMP_API_KEY and settings.MAILCHIMP_LIST_ID,
    }
