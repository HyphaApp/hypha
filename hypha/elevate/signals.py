"""
elevate.signals
~~~~~~~~~~~~~~~

:copyright: (c) 2017-present by Justin Mayer.
:copyright: (c) 2014-2016 by Matt Robenolt.
:license: BSD, see LICENSE for more details.
"""

from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

from .utils import grant_elevated_privileges, revoke_elevated_privileges


@receiver(user_logged_in)
def grant(sender, request, **kwargs):
    """
    Automatically grant elevated privileges when logging in.
    """
    grant_elevated_privileges(request)


@receiver(user_logged_out)
def revoke(sender, request, **kwargs):
    """
    Automatically revoke elevated privileges when logging out.
    """
    revoke_elevated_privileges(request)
