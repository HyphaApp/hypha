"""
elevate
~~~~

:copyright: (c) 2017-present by Justin Mayer.
:copyright: (c) 2014-2016 by Matt Robenolt.
:license: BSD, see LICENSE for more details.

2026-01-07: Moved in to hypha to avoid Setuptools complaining
about use of obsolete pkg_resources.
"""

from importlib.metadata import version

try:
    VERSION = version("elevate")
except Exception:  # pragma: no cover
    VERSION = "unknown"

default_app_config = "hypha.elevate.apps.ElevateConfig"
