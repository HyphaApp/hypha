"""
elevate.middleware
~~~~~~~~~~~~~~~~~~

:copyright: (c) 2017-present by Justin Mayer.
:copyright: (c) 2014-2016 by Matt Robenolt.
:license: BSD, see LICENSE for more details.
"""

from django.utils.deprecation import MiddlewareMixin
from elevate.settings import (
    COOKIE_DOMAIN,
    COOKIE_HTTPONLY,
    COOKIE_NAME,
    COOKIE_PATH,
    COOKIE_SALT,
    COOKIE_SECURE,
)
from elevate.utils import has_elevated_privileges


class ElevateMiddleware(MiddlewareMixin):
    """
    Middleware that contributes ``request.is_elevated()`` and sets the required
    cookie for Elevate mode to work correctly.
    """

    def has_elevated_privileges(self, request):
        # Override me to alter behavior
        return has_elevated_privileges(request)

    def process_request(self, request):
        assert hasattr(request, "session"), (
            "The Elevate middleware requires session middleware to be installed."
            "Edit your MIDDLEWARE_CLASSES setting to insert "
            "'django.contrib.sessions.middleware.SessionMiddleware' before "
            "'elevate.middleware.ElevateMiddleware'."
        )
        request.is_elevated = lambda: self.has_elevated_privileges(request)

    def process_response(self, request, response):
        is_elevated = getattr(request, "_elevate", None)

        if is_elevated is None:
            return response

        # We have explicitly had Elevate revoked, so clean up cookie
        if is_elevated is False and COOKIE_NAME in request.COOKIES:
            response.delete_cookie(COOKIE_NAME)
            return response

        # Elevate mode has been granted,
        # and we have a token to send back to the user agent
        if is_elevated is True and hasattr(request, "_elevate_token"):
            token = request._elevate_token
            max_age = request._elevate_max_age
            response.set_signed_cookie(
                COOKIE_NAME,
                token,
                salt=COOKIE_SALT,
                max_age=max_age,  # If max_age is None, it's a session cookie
                secure=request.is_secure() if COOKIE_SECURE is None else COOKIE_SECURE,
                httponly=COOKIE_HTTPONLY,  # Not accessible by JavaScript
                path=COOKIE_PATH,
                domain=COOKIE_DOMAIN,
            )

        return response
