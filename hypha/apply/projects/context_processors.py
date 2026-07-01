from django.conf import settings


def projects_enabled(request):
    return {
        "PROJECTS_ENABLED": settings.PROJECTS_ENABLED,
        "PROJECTS_ALLOW_MULTIPLE": settings.PROJECTS_ALLOW_MULTIPLE,
    }
