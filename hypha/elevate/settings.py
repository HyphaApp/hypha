"""
elevate.settings
~~~~~~~~~~~~~~~~

:copyright: (c) 2017-present by Justin Mayer.
:copyright: (c) 2014-2016 by Matt Robenolt.
:license: BSD, see LICENSE for more details.
"""

from django.conf import settings

# Default url to be redirected to after elevating permissions
REDIRECT_URL = getattr(settings, "ELEVATE_REDIRECT_URL", "/")

# The querystring argument to be used for redirection
REDIRECT_FIELD_NAME = getattr(settings, "ELEVATE_REDIRECT_FIELD_NAME", "next")

# How long should Elevate mode be active for? Duration in seconds.
COOKIE_AGE = getattr(settings, "ELEVATE_COOKIE_AGE", 10800)

# The domain to bind the Elevate cookie to. Default to the current domain.
COOKIE_DOMAIN = getattr(settings, "ELEVATE_COOKIE_DOMAIN", None)

# Should the cookie only be accessible via http requests?
# Note: If this is set to False, any JavaScript files have the ability to access this cookie,
# so this should only be changed if you have a good reason to do so.
COOKIE_HTTPONLY = getattr(settings, "ELEVATE_COOKIE_HTTPONLY", True)

# The name of the cookie to be used for Elevate mode.
COOKIE_NAME = getattr(settings, "ELEVATE_COOKIE_NAME", "elevate")

# Restrict the Elevate cookie to a specific path.
COOKIE_PATH = getattr(settings, "ELEVATE_COOKIE_PATH", "/")

# Only transmit the Elevate cookie over https if True.
# By default, this will match the current protocol. If your site is
# https already, this will be True.
COOKIE_SECURE = getattr(settings, "ELEVATE_COOKIE_SECURE", None)

# An extra salt to be added into the cookie signature
COOKIE_SALT = getattr(settings, "ELEVATE_COOKIE_SALT", "")

# The name of the session attribute used to preserve the redirect destination
# between the original page request and successful Elevate login.
REDIRECT_TO_FIELD_NAME = getattr(
    settings, "ELEVATE_REDIRECT_TO_FIELD_NAME", "elevate_redirect_to"
)

# The url for the Elevate page itself. May be a url or a view name
URL = getattr(settings, "ELEVATE_URL", "elevate.views.elevate")

# Length of the token stored in the cookie.
TOKEN_LENGTH = getattr(settings, "ELEVATE_TOKEN_LENGTH", 12)
