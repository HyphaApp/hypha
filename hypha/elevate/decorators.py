"""
elevate.decorators
~~~~~~~~~~~~~~~~~~

:copyright: (c) 2017-present by Justin Mayer.
:copyright: (c) 2014-2016 by Matt Robenolt.
:license: BSD, see LICENSE for more details.
"""

from functools import wraps

from elevate.views import redirect_to_elevate


def elevate_required(func):
    """
    Enforces a view to have elevated privileges.
    Should likely be paired with ``@login_required``.

    >>> @elevate_required
    >>> def secure_page(request):
    >>>     ...
    """

    @wraps(func)
    def inner(request, *args, **kwargs):
        if not request.is_elevated():
            return redirect_to_elevate(request.get_full_path())
        return func(request, *args, **kwargs)

    return inner
