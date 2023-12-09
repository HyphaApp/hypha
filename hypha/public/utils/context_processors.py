from hypha.public.home.models import HomePage


def global_vars(request):
    return {
        "PUBLIC_SITE": HomePage.objects.first().get_site(),
    }
