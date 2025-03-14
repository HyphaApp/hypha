from django import template
from django.utils.html import format_html_join

from extensions.django_hooks.templatehook import hook

register = template.Library()


@register.simple_tag(name="hook", takes_context=True)
def hook_tag(context, name, *args, **kwargs):
    r"""
    Hook tag to call within templates

    :param dict context: This is automatically passed,\
    contains the template state/variables
    :param str name: The hook which will be dispatched
    :param \*args: Positional arguments, will be passed to hook callbacks
    :param \*\*kwargs: Keyword arguments, will be passed to hook callbacks
    :return: A concatenation of all callbacks\
    responses marked as safe (conditionally)
    :rtype: str
    """
    return format_html_join(
        sep="\n",
        format_string="{}",
        args_generator=(
            (response,) for response in hook(name, context, *args, **kwargs)
        ),
    )


def template_hook_collect(module, hook_name, *args, **kwargs):
    r"""
    Helper to include in your own templatetag, for static TemplateHooks

    Example::

        import myhooks
        from hooks.templatetags import template_hook_collect

        @register.simple_tag(takes_context=True)
        def hook(context, name, *args, **kwargs):
            return template_hook_collect(myhooks, name, context, *args, **kwargs)

    :param module module: Module containing the template hook definitions
    :param str hook_name: The hook name to be dispatched
    :param \*args: Positional arguments, will be passed to hook callbacks
    :param \*\*kwargs: Keyword arguments, will be passed to hook callbacks
    :return: A concatenation of all callbacks\
    responses marked as safe (conditionally)
    :rtype: str
    """
    try:
        templatehook = getattr(module, hook_name)
    except AttributeError:
        return ""

    return format_html_join(
        sep="\n",
        format_string="{}",
        args_generator=((response,) for response in templatehook(*args, **kwargs)),
    )
