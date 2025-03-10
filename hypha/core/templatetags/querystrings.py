from urllib.parse import parse_qs, urlencode, urlparse

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag(takes_context=True)
def get_query(context, param):
    url = context.get("request").get_full_path()
    parsed_url = urlparse(url)
    captured_value = parse_qs(parsed_url.query)

    if captured_value and param in captured_value.keys():
        return captured_value[param][0]
    return None


def construct_query_string(context, query_params, only_query_string=False):
    # empty values will be removed
    query_string = "" if only_query_string else context["request"].path
    if len(query_params):
        query_params = sorted(
            query_params, key=lambda elem: "|".join([str(elem[0]), str(elem[1])])
        )
        encoded_params = urlencode(
            [(key, str(value)) for (key, value) in query_params if value]
        ).replace("&", "&amp;")
        query_string += "?{encoded_params}".format(encoded_params=encoded_params)
    return mark_safe(query_string)


@register.simple_tag(takes_context=True)
def modify_query(context, *params_to_remove, **params_to_change):
    """Renders a link with modified current query parameters"""
    only_query_string = False
    if "only_query_string" in params_to_remove:
        params_to_remove = [
            param for param in params_to_remove if param != "only_query_string"
        ]
        only_query_string = True
    query_params = []
    for key, value_list in context["request"].GET.lists():
        if key not in params_to_remove:
            # don't add key-value pairs for params_to_remove
            if key in params_to_change:
                # update values for keys in params_to_change
                query_params.append((key, params_to_change[key]))
                params_to_change.pop(key)
            else:
                # leave existing parameters as they were
                # if not mentioned in the params_to_change
                for value in value_list:
                    query_params.append((key, value))
                    # attach new params
    for key, value in params_to_change.items():
        query_params.append((key, value))
    return construct_query_string(
        context=context, query_params=query_params, only_query_string=only_query_string
    )


@register.simple_tag(takes_context=True)
def dup_modify_query(
    context, param_to_remove, param_key_to_change, param_value_to_change
):
    query_params = []
    param_key_used = False
    for key, value_list in context["request"].GET.lists():
        if key != param_to_remove:
            # don't add key-value pairs for params_to_remove
            if key == param_key_to_change:
                # update values for keys in params_to_change
                query_params.append((key, param_value_to_change))
                param_key_used = True
            else:
                # leave existing parameters as they were
                # if not mentioned in the params_to_change
                for value in value_list:
                    query_params.append((key, value))
                    # attach new params
    if not param_key_used:
        query_params.append((param_key_to_change, param_value_to_change))
    return construct_query_string(
        context=context, query_params=query_params, only_query_string=False
    )


@register.simple_tag(takes_context=True)
def add_to_query(context, *params_to_remove, **params_to_add):
    """Renders a link with modified current query parameters"""
    only_query_string = False
    if "only_query_string" in params_to_remove:
        params_to_remove = [
            param for param in params_to_remove if param != "only_query_string"
        ]
        only_query_string = True
    query_params = []
    # go through current query params..
    for key, value_list in context["request"].GET.lists():
        if key not in params_to_remove:
            # don't add key-value pairs which already
            # exist in the query
            if key in params_to_add and params_to_add[key] in value_list:
                params_to_add.pop(key)
            for value in value_list:
                query_params.append((key, value))
    # add the rest key-value pairs
    for key, value in params_to_add.items():
        query_params.append((key, value))
    return construct_query_string(
        context=context, query_params=query_params, only_query_string=only_query_string
    )


@register.simple_tag(takes_context=True)
def dup_add_to_query(
    context,
    param_to_remove,
    param_key_to_add,
    param_value_to_add,
    only_query_string=False,
):
    """Renders a link with modified current query parameters"""
    query_params = []
    param_key_used = False
    # go through current query params..
    for key, value_list in context["request"].GET.lists():
        if key != param_to_remove:
            # don't add key-value pairs which already
            # exist in the query
            if key == param_key_to_add and param_value_to_add in value_list:
                param_key_used = True
            for value in value_list:
                query_params.append((key, value))
    # add the rest key-value pairs
    if not param_key_used:
        query_params.append((param_key_to_add, param_value_to_add))
    return construct_query_string(
        context=context, query_params=query_params, only_query_string=only_query_string
    )


@register.simple_tag(takes_context=True)
def remove_from_query(context, *args, **kwargs):
    """Renders a link with modified current query parameters"""
    only_query_string = False
    if "only_query_string" in args:
        args = [param for param in args if param != "only_query_string"]
        only_query_string = True
    query_params = []
    # go through current query params..
    for key, value_list in context["request"].GET.lists():
        # skip keys mentioned in the args
        if key not in args:
            for value in value_list:
                # skip key-value pairs mentioned in kwargs
                if not (key in kwargs and str(value) == str(kwargs[key])):
                    query_params.append((key, value))
    return construct_query_string(
        context=context, query_params=query_params, only_query_string=only_query_string
    )


@register.simple_tag(takes_context=True)
def dup_remove_from_query(
    context, param_to_remove, param_key_to_remove, param_value_to_remove
):
    query_params = []
    # go through current query params..
    for key, value_list in context["request"].GET.lists():
        # skip keys mentioned in the args
        if key != param_to_remove:
            for value in value_list:
                # skip key-value pairs mentioned in kwargs
                if not (
                    key == param_key_to_remove
                    and str(value) == str(param_value_to_remove)
                ):
                    query_params.append((key, value))
    return construct_query_string(
        context=context, query_params=query_params, only_query_string=False
    )
