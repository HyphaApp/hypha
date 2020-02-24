from django.conf import settings


def projects_enabled(request):
    return {'PROJECTS_ENABLED': settings.PROJECTS_ENABLED}
