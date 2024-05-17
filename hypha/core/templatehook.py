# Adds the ability to have hooks injected into templates, via the `hooks_tags.hook` template tag.
# 
# Originally from https://github.com/nitely/django-hooks but after culling everything except
# the template hook.  See /docs/templatehook.rst for more information
# 
# The reason this was forked, rather than used as a module, is that the last commit from the
# other project was made in 2015, and can no longer be imported into a modern django project.
# The template hook continues to work correctly, but the other hooks most likely do not, and
# so were removed.

class TemplateHook(object):
    """
    A hook for templates. This can be used directly or\
    through the :py:class:`Hook` dispatcher

    :param list providing_args: A list of the arguments\
    this hook can pass along in a :py:func:`.__call__`
    """

    def __init__(self, providing_args=None):
        self.providing_args = providing_args or []
        self._registry = []

    def __call__(self, *args, **kwargs):
        """
        Collect all callbacks responses for this template hook

        :return: Responses by registered callbacks,\
        this is usually a list of HTML strings
        :rtype: list
        """
        return [func(*args, **kwargs) for func in self._registry]

    def register(self, func):
        """
        Register a new callback

        :param callable func: A function reference used as a callback
        """
        assert callable(func), "Callback func must be a callable"

        self._registry.append(func)

    def unregister(self, func):
        """
        Remove a previously registered callback

        :param callable func: A function reference\
        that was registered previously
        """
        try:
            self._registry.remove(func)
        except ValueError:
            pass

    def unregister_all(self):
        """
        Remove all callbacks
        """
        del self._registry[:]


class Hook(object):
    """
    Dynamic dispatcher (proxy) for :py:class:`TemplateHook`
    """

    def __init__(self):
        self._registry = {}

    def __call__(self, name, *args, **kwargs):
        """
        Collect all callbacks responses for this template hook.\
        The hook (name) does not need to be pre-created,\
        it may not exist at call time

        :param str name: Hook name, it must be unique,\
        prefixing it with the app label is a good idea
        :return: Responses by registered callbacks
        :rtype: list
        """
        try:
            templatehook = self._registry[name]
        except KeyError:
            return []

        return templatehook(*args, **kwargs)

    def _register(self, name):
        """
        @Api private
        Add new :py:class:`TemplateHook` into the registry

        :param str name: Hook name
        :return: Instance of :py:class:`TemplateHook`
        :rtype: :py:class:`TemplateHook`
        """
        templatehook = TemplateHook()
        self._registry[name] = templatehook
        return templatehook

    def register(self, name, func):
        """
        Register a new callback.\
        When the name/id is not found\
        a new hook is created under its name,\
        meaning the hook is usually created by\
        the first registered callback

        :param str name: Hook name
        :param callable func: A func reference (callback)
        """
        try:
            templatehook = self._registry[name]
        except KeyError:
            templatehook = self._register(name)

        templatehook.register(func)

    def unregister(self, name, func):
        """
        Remove a previously registered callback

        :param str name: Hook name
        :param callable func: A function reference\
        that was registered previously
        """
        try:
            templatehook = self._registry[name]
        except KeyError:
            return

        templatehook.unregister(func)

    def unregister_all(self, name):
        """
        Remove all callbacks

        :param str name: Hook name
        """
        try:
            templatehook = self._registry[name]
        except KeyError:
            return

        templatehook.unregister_all()


hook = Hook()
