from django.template.loader import render_to_string


def wagtail_user_edit(context, *args, **kwargs):
    return render_to_string(
        "wagtail_user_edit.html",
        context.flatten(),
    )


def hypha_extension_head(context, *args, **kwargs):
    return render_to_string(
        "hypha_extension_head.html",
        context.flatten(),
    )
