Hypha implements DJP: Django Plugins. A plugin system for Django.

See https://djp.readthedocs.io/ for more information.

## Some tips

You can set the `DJP_PLUGINS_DIR` environment variable to point to a directory which contains *.py files implementing plugins. Good for development and when you do not want to publish the plugin on PyPI.

Since DJP allow a plugin to override any setting you can tell Hypha to look for templates in a directory inside your plugin. This allows the plugin to override any template in Hypha.

## URL ordering

URLs contributed through the DJP `urlpatterns()` hook are added to the root urlconf **after** Hypha's own routes but **before** Wagtail's page-serving catch-all (`path("", include(wagtail_urls))`). This means:

- A plugin **cannot** shadow a core Hypha URL (e.g. `apply/`, `admin/`, `account/`) — core routes are matched first.
- A plugin URL **is** reachable even when it is slug-shaped (e.g. `account/country/`). Wagtail's catch-all would otherwise match any such path and return a 404 (*"The current path … matched the last one."*), so plugin URLs are deliberately placed ahead of it.
- A plugin URL takes precedence over a Wagtail page at the same path.

Prefer the `urlpatterns()` hook for adding routes. Only manipulate the root urlconf directly (e.g. from `AppConfig.ready()`) if you need finer control than the hook provides.
