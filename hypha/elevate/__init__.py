"""
elevate
~~~~

:copyright: (c) 2017-present by Justin Mayer.
:copyright: (c) 2014-2016 by Matt Robenolt.
:license: BSD, see LICENSE for more details.
"""

from importlib.metadata import version

try:
    VERSION = version("elevate")
except Exception:  # pragma: no cover
    VERSION = "unknown"

default_app_config = "elevate.apps.ElevateConfig"
