# django_hooks

Adds the ability to have hooks injected into templates, via the `hooks_tags.hook` template tag.

Originally from https://github.com/nitely/django-hooks but after culling everything except the template hook.  The documentation on that template hook at [readthedocs](https://django-hooks.readthedocs.io/en/latest/hooks.html#templatehook) is [replicated locally](docs/templatehook.rst)

The reason this was forked, rather than used as a module, is that the last commit from the other project was made in 2015, and can no longer be imported into a modern django project.  The template hook continues to work correctly, but the other hooks most likely do not, and so were removed.
