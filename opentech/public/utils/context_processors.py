from opentech.apply.home.models import ApplyHomePage
from opentech.public.home.models import HomePage

from opentech.public.mailchimp.forms import NewsletterForm


def global_vars(request):
    return {
        'APPLY_SITE': ApplyHomePage.objects.first().get_site(),
        'PUBLIC_SITE': HomePage.objects.first().get_site(),
        'newsletter_form': NewsletterForm()
    }
