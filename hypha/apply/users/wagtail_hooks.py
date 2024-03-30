from django.urls import re_path
from wagtail import hooks
from wagtail.models import Site

from hypha.apply.activity.messaging import MESSAGES, messenger

from .admin_views import CustomGroupViewSet, CustomUserIndexView
from .utils import send_activation_email


@hooks.register("register_admin_urls")
def register_admin_urls():
    return [
        re_path(r"^users/$", CustomUserIndexView.as_view(), name="index"),
    ]


@hooks.register("register_admin_viewset")
def register_viewset():
    return CustomGroupViewSet("groups", url_prefix="groups")


@hooks.register("after_create_user")
def notify_after_create_user(request, user):
    messenger(
        MESSAGES.STAFF_ACCOUNT_CREATED,
        request=request,
        user=request.user,
        source=user,
    )

    site = Site.find_for_request(request)
    send_activation_email(user, site)


@hooks.register("after_edit_user")
def notify_after_edit_user(request, user):
    roles = list(user.groups.values_list("name", flat=True))
    if user.is_superuser:
        roles.append("Administrator")
    if roles:
        roles = ", ".join(roles)
        messenger(
            MESSAGES.STAFF_ACCOUNT_EDITED,
            request=request,
            user=request.user,
            source=user,
            roles=roles,
        )
