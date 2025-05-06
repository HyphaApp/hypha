from django.conf import settings
from django.http import Http404
from django.urls import Resolver404, resolve


class ProjectsEnabledMiddleware:
    """
    Middleware to control access to project urls based on PROJECTS_ENABLED setting.

    This makes the decision at runtime rather than at URL pattern registration time,
    avoiding potential issues with module loading order and settings configuration.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip processing if PROJECTS_ENABLED is true
        if settings.PROJECTS_ENABLED:
            return self.get_response(request)

        # Check if the current URL is in the projects namespace
        try:
            resolver_match = resolve(request.path)
            if "projects" in getattr(resolver_match, "namespaces", []):
                raise Http404("Projects functionality is disabled")
        except Resolver404:
            # Not a URL we can resolve, let Django handle it
            pass

        # Continue processing the request
        return self.get_response(request)
