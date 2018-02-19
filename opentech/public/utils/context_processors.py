from django.conf import settings

from opentech.apply.home.models import ApplyHomePage


def global_vars(request):
    return {
        'GOOGLE_TAG_MANAGER_ID': getattr(settings, 'GOOGLE_TAG_MANAGER_ID', None),
        'APPLY_SITE': ApplyHomePage.objects.first(),
    }
