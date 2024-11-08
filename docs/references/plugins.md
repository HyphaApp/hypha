Hypha implements DJP: Django Plugins. A plugin system for Django.

See https://djp.readthedocs.io/ for more information.

## Some tips

You can set the `DJP_PLUGINS_DIR` environment variable to point to a directory which contains *.py files implementing plugins. Good for development and when you do not want to publish the plugin on PyPI.

Since DJP allow a plugin to override any setting you can tell Hypha to look for templates in a directory inside your plugin. This allows the plugin to override any template in Hypha.
