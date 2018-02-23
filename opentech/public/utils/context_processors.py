from django.conf import settings

from opentech.apply.home.models import ApplyHomePage
from opentech.public.home.models import HomePage


def global_vars(request):
    return {
        'GOOGLE_TAG_MANAGER_ID': getattr(settings, 'GOOGLE_TAG_MANAGER_ID', None),
        'APPLY_SITE': ApplyHomePage.objects.first().get_site(),
        'PUBLIC_SITE': HomePage.objects.first().get_site(),
    }
