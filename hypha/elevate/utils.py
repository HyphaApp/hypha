"""
elevate.utils
~~~~~~~~~~~~~

:copyright: (c) 2017-present by Justin Mayer.
:copyright: (c) 2014-2016 by Matt Robenolt.
:license: BSD, see LICENSE for more details.
"""

from django.core.signing import BadSignature
from django.utils.crypto import constant_time_compare, get_random_string
from elevate.settings import COOKIE_AGE, COOKIE_NAME, COOKIE_SALT, TOKEN_LENGTH


def grant_elevated_privileges(request, max_age=COOKIE_AGE):
    """
    Assigns a random token to the user's session
    that allows them to have elevated permissions
    """
    user = getattr(request, "user", None)

    # If there's not a user on the request, just noop
    if user is None:
        return

    if not user.is_authenticated:
        raise ValueError("User needs to be logged in to be elevated")

    # Token doesn't need to be unique,
    # just needs to be unpredictable and match the cookie and the session
    token = get_random_string(TOKEN_LENGTH)
    request.session[COOKIE_NAME] = token
    request._elevate = True
    request._elevate_token = token
    request._elevate_max_age = max_age
    return token


def revoke_elevated_privileges(request):
    """
    Revoke elevated privileges from a request explicitly
    """
    request._elevate = False
    if COOKIE_NAME in request.session:
        del request.session[COOKIE_NAME]


def has_elevated_privileges(request):
    """
    Check if a request is allowed to perform Elevate actions
    """
    if getattr(request, "_elevate", None) is None:
        try:
            request._elevate = request.user.is_authenticated and constant_time_compare(
                request.get_signed_cookie(
                    COOKIE_NAME, salt=COOKIE_SALT, max_age=COOKIE_AGE
                ),
                request.session[COOKIE_NAME],
            )
        except (KeyError, BadSignature):
            request._elevate = False
    return request._elevate
